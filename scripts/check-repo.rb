#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "tmpdir"
require "uri"
require "yaml"

ROOT = File.expand_path("..", __dir__)
Dir.chdir(ROOT)

errors = []
error = ->(message) { errors << message }
paths = `git ls-files -co --exclude-standard -z`.split("\0").uniq
text_paths = paths.select { |path| File.file?(path) && %w[.md .txt .yaml .yml .json .rb .sh].include?(File.extname(path)) }

skill_records = Dir.glob("plugins/*/skills/*/SKILL.md").sort.map do |path|
  text = File.read(path)
  match = text.match(/\A---\s*\n(.*?)\n---\s*\n/m)
  unless match
    error.call("#{path}: missing YAML frontmatter")
    next
  end

  begin
    data = YAML.safe_load(match[1], permitted_classes: [], aliases: false) || {}
  rescue Psych::SyntaxError => e
    error.call("#{path}: invalid YAML frontmatter: #{e.problem}")
    next
  end

  plugin = path.split("/")[1]
  directory = File.basename(File.dirname(path))
  name = data["name"]
  error.call("#{path}: name must match directory #{directory.inspect}") unless name == directory
  error.call("#{path}: name must be lowercase kebab-case") unless name.is_a?(String) && name.match?(/\A[a-z0-9]+(?:-[a-z0-9]+)*\z/)
  error.call("#{path}: description must be nonempty") unless data["description"].is_a?(String) && !data["description"].strip.empty?
  error.call("#{path}: argument-hint is host-specific") if data.key?("argument-hint")

  normalized_text = text.gsub(/\s+/, " ")
  blanket_stop = /\bif you encounter any error\b.{0,80}\bstop\b/i
  if plugin == "spex" && normalized_text.match?(blanket_stop)
    error.call("#{path}: blanket stop-on-error policy; distinguish recoverable failures from genuine blockers")
  end

  if data["disable-model-invocation"] == true
    policy_path = File.join(File.dirname(path), "agents/openai.yaml")
    if !File.file?(policy_path)
      error.call("#{path}: disable-model-invocation requires agents/openai.yaml")
    else
      policy = YAML.safe_load(File.read(policy_path), permitted_classes: [], aliases: false) || {}
      unless policy.dig("policy", "allow_implicit_invocation") == false
        error.call("#{policy_path}: must set policy.allow_implicit_invocation to false")
      end
    end
  end

  body = text[match.end(0)..]
  owns_config = body.include?(".agents/skill-configs/#{name}/") || body.include?(".agents/skill-configs/#{plugin}/")
  if owns_config && !File.file?(File.join(File.dirname(path), "config.example.yaml"))
    error.call("#{path}: configured skill must ship adjacent config.example.yaml")
  end

  { path: path, plugin: plugin, name: name, text: text }
rescue Psych::SyntaxError => e
  error.call("#{path}: invalid agents/openai.yaml: #{e.problem}")
  nil
end.compact

Dir.glob("plugins/*/skills/*").select { |path| File.directory?(path) }.each do |directory|
  next if File.file?(File.join(directory, "SKILL.md"))
  next if Dir.children(directory).empty?

  error.call("#{directory}: contains files but no SKILL.md")
end

Dir.glob("plugins/**/config.example.yaml").sort.each do |path|
  YAML.safe_load(File.read(path), permitted_classes: [], aliases: false)
rescue Psych::SyntaxError => e
  error.call("#{path}: invalid YAML: #{e.problem}")
end

macros_config = "plugins/macros/config.example.yaml"
if File.file?(macros_config)
  skill_records.select { |skill| skill[:plugin] == "macros" && skill[:text].include?(".agents/skill-configs/macros/") }.each do |skill|
    copy = File.join(File.dirname(skill[:path]), "config.example.yaml")
    error.call("#{copy}: must match #{macros_config}") if File.file?(copy) && File.binread(copy) != File.binread(macros_config)
  end
end

portable_docs = text_paths.select { |path| %w[.md .txt].include?(File.extname(path)) }
portable_docs.each do |path|
  File.foreach(path).with_index(1) do |line, number|
    error.call("#{path}:#{number}: command-like skill(...) reference") if line.include?("skill(")
    error.call("#{path}:#{number}: Claude-specific skill directory variable") if line.include?("${CLAUDE_SKILL_DIR}")
  end
end

named_tools = /\b(?:AskUserQuestion|WebSearch|WebFetch|Agent tool|Edit tool)\b/
skill_records.each do |skill|
  skill[:text].each_line.with_index(1) do |line, number|
    error.call("#{skill[:path]}:#{number}: named host tool; use capability language") if line.match?(named_tools)
  end
end

skill_names = skill_records.flat_map { |skill| [skill[:name], "#{skill[:plugin]}:#{skill[:name]}"] }.uniq.sort_by { |name| -name.length }
selector = /(?<![A-Za-z0-9_.\/-])[\/$@](?:#{skill_names.map { |name| Regexp.escape(name) }.join("|")})(?![A-Za-z0-9_:-])/
portable_docs.reject { |path| path.start_with?("docs/cross-platform/") }.each do |path|
  File.foreach(path).with_index(1) do |line, number|
    error.call("#{path}:#{number}: host-specific skill selector belongs in docs/cross-platform") if line.match?(selector)
  end
end

install_roots = [
  ".agents/skills/", "~/.agents/skills/", ".gemini/skills/", "~/.gemini/skills/",
  ".claude/skills/", ".cursor/skills/", "~/.config/agents/skills/",
  "~/.config/amp/skills/", "~/.gemini/config/skills/"
]
portable_docs.reject { |path| path == "docs/cross-platform/README.md" }.each do |path|
  File.foreach(path).with_index(1) do |line, number|
    root = install_roots.find { |candidate| line.include?(candidate) }
    error.call("#{path}:#{number}: provider install root #{root.inspect} belongs in the compatibility SSOT") if root
  end
end

marketplace = JSON.parse(File.read(".claude-plugin/marketplace.json"))
marketplace.fetch("plugins").each do |entry|
  name = entry.fetch("name")
  source = entry.fetch("source").sub(%r{\A\./}, "")
  manifest_path = File.join(source, ".claude-plugin/plugin.json")
  unless File.file?(manifest_path)
    error.call("#{manifest_path}: missing marketplace plugin manifest")
    next
  end

  manifest = JSON.parse(File.read(manifest_path))
  error.call("#{manifest_path}: name must match marketplace entry #{name.inspect}") unless manifest["name"] == name
  error.call("#{manifest_path}: version must be semver") unless manifest["version"].is_a?(String) && manifest["version"].match?(/\A\d+\.\d+\.\d+\z/)
end

markdown_paths = paths.select { |path| File.file?(path) && File.extname(path) == ".md" }
markdown_paths.each do |path|
  in_fence = false
  File.foreach(path) do |line|
    if line.lstrip.match?(/\A(?:```|~~~)/)
      in_fence = !in_fence
      next
    end
    next if in_fence

    line.scan(/!?\[[^\]]*\]\(([^)]+)\)/).flatten.each do |target|
      target = target.strip
      target = target[1..-2] if target.start_with?("<") && target.end_with?(">")
      target = target.split(/\s+["']/, 2).first
      next if target.empty? || target.start_with?("#") || target.match?(%r{\A(?:https?|mailto|data):}i)
      next if target.match?(/[{}$*]/)

      local = URI::DEFAULT_PARSER.unescape(target.split("#", 2).first)
      resolved = File.expand_path(local, File.dirname(path))
      error.call("#{path}: broken local link #{target.inspect}") unless File.exist?(resolved)
    end
  end
end

paths.select { |path| File.symlink?(path) }.each do |path|
  error.call("#{path}: broken symlink") unless File.exist?(path)
end

text_paths.each do |path|
  File.foreach(path).with_index(1) do |line, number|
    error.call("#{path}:#{number}: trailing whitespace") if line.match?(/[ \t]+(?:\r?\n)?\z/) && !line.match?(/\A[ \t]*\r?\n\z/)
    error.call("#{path}:#{number}: unresolved merge marker") if line.match?(/\A(?:<{7}|={7}|>{7})(?: |$)/)
  end
end

Dir.mktmpdir("plugin-pack-check") do |output|
  marketplace.fetch("plugins").each do |entry|
    name = entry.fetch("name")
    unless system("bash", "scripts/pack-plugin.sh", name, output, out: File::NULL, err: File::NULL)
      error.call("plugins/#{name}: pack-plugin.sh failed")
      next
    end
    archive = File.join(output, "#{name}.zip")
    error.call("#{archive}: package was not created") unless File.file?(archive) && File.size?(archive)
  end
end

if errors.empty?
  puts "repository checks: OK (#{skill_records.length} skills, #{marketplace.fetch('plugins').length} marketplace plugins)"
else
  warn errors.uniq.sort.join("\n")
  warn "repository checks: #{errors.uniq.length} failure(s)"
  exit 1
end
