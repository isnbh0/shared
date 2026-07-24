use roxmltree::{Document, Node, ParsingOptions};
use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process;

const DSL_NS: &str = "urn:labs:pictogram:1";
const CANON_NS: &str = "urn:labs:pictogram:canon:1";
const DEFAULT_CANON: &str = "canon/aicher-inspired-48-v1.xml";

#[derive(Clone, Copy, Debug)]
struct Point {
    x: i32,
    y: i32,
}

#[derive(Debug)]
struct Bone {
    role: String,
    from: String,
    to: String,
    min_length: f64,
    max_length: f64,
    layer: String,
}

#[derive(Debug)]
struct Canon {
    id: String,
    width: i32,
    height: i32,
    grid_step: i32,
    safe_margin: i32,
    head_radius: i32,
    body_width: f64,
    equipment_width: f64,
    palette: HashMap<String, String>,
    directions: HashMap<(i32, i32), u32>,
    bones: Vec<Bone>,
    layers: Vec<String>,
    max_actors: usize,
    max_assemblies: usize,
    max_primitives: usize,
    max_expression_cost: u32,
}

#[derive(Debug)]
struct Actor {
    id: String,
    facing: String,
    head: Point,
    joints: HashMap<String, Point>,
}

#[derive(Debug)]
enum Primitive {
    Bar {
        start: Point,
        end: Point,
    },
    Disc {
        center: Point,
        radius: i32,
    },
    Ring {
        center: Point,
        radius: i32,
    },
    Box {
        origin: Point,
        width: i32,
        height: i32,
    },
    Wedge {
        points: [Point; 3],
    },
}

#[derive(Debug)]
struct Assembly {
    id: String,
    role: String,
    layer: String,
    color_role: String,
    primitives: Vec<Primitive>,
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
struct Deviation {
    feature: String,
    target: String,
    cost: u32,
}

#[derive(Debug)]
struct Pictogram {
    id: String,
    profile: String,
    title: String,
    description: String,
    verb: String,
    direction: String,
    actors: Vec<Actor>,
    assemblies: Vec<Assembly>,
    declared_deviations: Vec<Deviation>,
}

#[derive(Debug)]
struct Validated {
    pictogram: Pictogram,
    canon: Canon,
    deviations: BTreeSet<Deviation>,
    warnings: Vec<String>,
}

fn main() {
    if let Err(message) = run() {
        eprintln!("error: {message}");
        process::exit(1);
    }
}

fn run() -> Result<(), String> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 3 {
        return Err(usage());
    }

    let command = args[1].as_str();
    let (input, output, canon_path) = match command {
        "validate" => {
            let (input, canon) = parse_validate_args(&args[2..])?;
            (input, None, canon)
        }
        "compile" => {
            let (input, output, canon) = parse_compile_args(&args[2..])?;
            (input, Some(output), canon)
        }
        _ => return Err(usage()),
    };

    let source = fs::read_to_string(&input)
        .map_err(|error| format!("cannot read {}: {error}", input.display()))?;
    let canon_source = fs::read_to_string(&canon_path)
        .map_err(|error| format!("cannot read {}: {error}", canon_path.display()))?;
    let validated = validate_document(&source, &canon_source)?;

    for warning in &validated.warnings {
        eprintln!("warning: {warning}");
    }

    match command {
        "validate" => {
            let cost: u32 = validated.deviations.iter().map(|item| item.cost).sum();
            println!(
                "OK: {} (profile {}; expression cost {}/{})",
                validated.pictogram.id,
                validated.pictogram.profile,
                cost,
                validated.canon.max_expression_cost
            );
        }
        "compile" => {
            let output = output.expect("compile output");
            let svg = compile_svg(&validated);
            write_output(&output, &svg)?;
            println!("wrote {}", output.display());
        }
        _ => unreachable!(),
    }
    Ok(())
}

fn usage() -> String {
    [
        "usage:",
        "  pictogram validate <source.xml> [--canon <canon.xml>]",
        "  pictogram compile <source.xml> <output.svg> [--canon <canon.xml>]",
    ]
    .join("\n")
}

fn parse_validate_args(args: &[String]) -> Result<(PathBuf, PathBuf), String> {
    if args.is_empty() {
        return Err(usage());
    }
    let input = PathBuf::from(&args[0]);
    let canon = parse_canon_option(&args[1..])?;
    Ok((input, canon))
}

fn parse_compile_args(args: &[String]) -> Result<(PathBuf, PathBuf, PathBuf), String> {
    if args.len() < 2 {
        return Err(usage());
    }
    let input = PathBuf::from(&args[0]);
    let output = PathBuf::from(&args[1]);
    let canon = parse_canon_option(&args[2..])?;
    Ok((input, output, canon))
}

fn parse_canon_option(args: &[String]) -> Result<PathBuf, String> {
    if args.is_empty() {
        return Ok(Path::new(env!("CARGO_MANIFEST_DIR")).join(DEFAULT_CANON));
    }
    if args.len() == 2 && args[0] == "--canon" {
        return Ok(PathBuf::from(&args[1]));
    }
    Err(usage())
}

fn validate_document(source: &str, canon_source: &str) -> Result<Validated, String> {
    let canon = parse_canon(canon_source)?;
    let pictogram = parse_pictogram(source)?;
    if pictogram.profile != canon.id {
        return Err(format!(
            "profile {:?} does not match canon {:?}",
            pictogram.profile, canon.id
        ));
    }

    let mut errors = Vec::new();
    let mut warnings = Vec::new();
    let mut derived = BTreeSet::new();

    if pictogram.actors.len() > canon.max_actors {
        errors.push(format!(
            "scene has {} actors; profile maximum is {}",
            pictogram.actors.len(),
            canon.max_actors
        ));
    }
    if pictogram.assemblies.len() > canon.max_assemblies {
        errors.push(format!(
            "scene has {} assemblies; profile maximum is {}",
            pictogram.assemblies.len(),
            canon.max_assemblies
        ));
    }
    if pictogram.actors.is_empty()
        && !pictogram
            .assemblies
            .iter()
            .any(|assembly| assembly.role == "subject")
    {
        errors.push("scene needs an actor or an assembly with role=\"subject\"".to_string());
    }
    if pictogram.actors.len() == 2 {
        derived.insert(Deviation {
            feature: "second-actor".to_string(),
            target: "scene".to_string(),
            cost: 2,
        });
    }

    let required_joints: BTreeSet<&str> = [
        "shoulder",
        "hip",
        "elbow-near",
        "hand-near",
        "elbow-far",
        "hand-far",
        "knee-near",
        "foot-near",
        "knee-far",
        "foot-far",
    ]
    .into_iter()
    .collect();

    for actor in &pictogram.actors {
        let actual: BTreeSet<&str> = actor.joints.keys().map(String::as_str).collect();
        if actual != required_joints {
            let missing: Vec<_> = required_joints.difference(&actual).copied().collect();
            let extra: Vec<_> = actual.difference(&required_joints).copied().collect();
            errors.push(format!(
                "actor {} has wrong joint set (missing: {}; extra: {})",
                actor.id,
                display_list(&missing),
                display_list(&extra)
            ));
            continue;
        }

        let mut points = vec![actor.head];
        points.extend(actor.joints.values().copied());
        validate_points(&actor.id, &points, &canon, true, &mut errors, &mut derived);

        let head_left = actor.head.x - canon.head_radius;
        let head_right = actor.head.x + canon.head_radius;
        let head_top = actor.head.y - canon.head_radius;
        let head_bottom = actor.head.y + canon.head_radius;
        if head_left < canon.safe_margin
            || head_right > canon.width - canon.safe_margin
            || head_top < canon.safe_margin
            || head_bottom > canon.height - canon.safe_margin
        {
            errors.push(format!("actor {} head crosses the safe margin", actor.id));
        }

        for bone in &canon.bones {
            let start = actor.joints[&bone.from];
            let end = actor.joints[&bone.to];
            let dx = end.x - start.x;
            let dy = end.y - start.y;
            if dx == 0 && dy == 0 {
                errors.push(format!(
                    "actor {} bone {} has zero length",
                    actor.id, bone.role
                ));
                continue;
            }
            let divisor = gcd(dx.abs(), dy.abs());
            let direction = (dx / divisor, dy / divisor);
            match canon.directions.get(&direction) {
                Some(0) => {}
                Some(cost) => {
                    derived.insert(Deviation {
                        feature: "extended-vector".to_string(),
                        target: format!("{}:{}", actor.id, bone.role),
                        cost: *cost,
                    });
                }
                None => errors.push(format!(
                    "actor {} bone {} uses unsupported direction {}:{}",
                    actor.id, bone.role, direction.0, direction.1
                )),
            }

            let length = ((dx * dx + dy * dy) as f64).sqrt();
            if length < bone.min_length || length > bone.max_length {
                errors.push(format!(
                    "actor {} bone {} length {} is outside {}..{}",
                    actor.id,
                    bone.role,
                    format_number(length),
                    format_number(bone.min_length),
                    format_number(bone.max_length)
                ));
            }
        }

        let shoulder = actor.joints["shoulder"];
        let head_gap = distance(actor.head, shoulder) - canon.head_radius as f64;
        if head_gap > canon.body_width * 1.5 {
            warnings.push(format!(
                "actor {} head is visually detached from the torso",
                actor.id
            ));
        }
        if actor.joints["hand-near"].x == actor.joints["hand-far"].x
            && actor.joints["hand-near"].y == actor.joints["hand-far"].y
        {
            warnings.push(format!("actor {} hands overlap exactly", actor.id));
        }
        if actor.joints["foot-near"].x == actor.joints["foot-far"].x
            && actor.joints["foot-near"].y == actor.joints["foot-far"].y
        {
            warnings.push(format!("actor {} feet overlap exactly", actor.id));
        }
    }

    for assembly in &pictogram.assemblies {
        if assembly.primitives.len() > canon.max_primitives {
            errors.push(format!(
                "assembly {} has {} primitives; profile maximum is {}",
                assembly.id,
                assembly.primitives.len(),
                canon.max_primitives
            ));
        }
        if !canon.layers.contains(&assembly.layer) {
            errors.push(format!(
                "assembly {} uses unknown layer {}",
                assembly.id, assembly.layer
            ));
        }
        if !canon.palette.contains_key(&assembly.color_role) {
            errors.push(format!(
                "assembly {} uses unknown color role {}",
                assembly.id, assembly.color_role
            ));
        }
        derived.insert(Deviation {
            feature: "custom-assembly".to_string(),
            target: assembly.id.clone(),
            cost: 1,
        });

        let mut points = Vec::new();
        for primitive in &assembly.primitives {
            match primitive {
                Primitive::Bar { start, end } => {
                    points.extend([*start, *end]);
                    if start.x == end.x && start.y == end.y {
                        errors.push(format!(
                            "assembly {} contains a zero-length bar",
                            assembly.id
                        ));
                    }
                }
                Primitive::Disc { center, radius } | Primitive::Ring { center, radius } => {
                    points.push(*center);
                    if *radius <= 0 {
                        errors.push(format!(
                            "assembly {} contains a non-positive radius",
                            assembly.id
                        ));
                    }
                    if center.x - radius < 0
                        || center.y - radius < 0
                        || center.x + radius > canon.width
                        || center.y + radius > canon.height
                    {
                        errors.push(format!(
                            "assembly {} contains a circle outside the canvas",
                            assembly.id
                        ));
                    }
                }
                Primitive::Box {
                    origin,
                    width,
                    height,
                } => {
                    points.push(*origin);
                    points.push(Point {
                        x: origin.x + width,
                        y: origin.y + height,
                    });
                    if *width <= 0 || *height <= 0 {
                        errors.push(format!(
                            "assembly {} contains a non-positive box",
                            assembly.id
                        ));
                    }
                }
                Primitive::Wedge { points: wedge } => points.extend(wedge),
            }
        }
        validate_points(
            &assembly.id,
            &points,
            &canon,
            false,
            &mut errors,
            &mut derived,
        );
    }

    validate_declarations(
        &pictogram.declared_deviations,
        &derived,
        canon.max_expression_cost,
        &mut errors,
    );

    if errors.is_empty() {
        Ok(Validated {
            pictogram,
            canon,
            deviations: derived,
            warnings,
        })
    } else {
        Err(errors.join("\n"))
    }
}

fn parse_pictogram(source: &str) -> Result<Pictogram, String> {
    let options = ParsingOptions {
        allow_dtd: false,
        ..ParsingOptions::default()
    };
    let document = Document::parse_with_options(source, options)
        .map_err(|error| format!("invalid pictogram XML: {error}"))?;
    let root = document.root_element();
    expect_element(root, "pictogram", DSL_NS)?;
    check_attributes(root, &["id", "profile"])?;

    let id = required_attr(root, "id")?.to_string();
    validate_identifier(&id, "pictogram id")?;
    let profile = required_attr(root, "profile")?.to_string();
    let children = element_children(root);
    if !(children.len() == 3 || children.len() == 4) {
        return Err(
            "pictogram requires metadata, intent, scene, and optional expression".to_string(),
        );
    }
    expect_element(children[0], "metadata", DSL_NS)?;
    expect_element(children[1], "intent", DSL_NS)?;
    expect_element(children[2], "scene", DSL_NS)?;
    if children.len() == 4 {
        expect_element(children[3], "expression", DSL_NS)?;
    }

    let (title, description) = parse_metadata(children[0])?;
    let (verb, direction) = parse_intent(children[1])?;
    let (actors, assemblies) = parse_scene(children[2])?;
    let declared_deviations = if children.len() == 4 {
        parse_expression(children[3])?
    } else {
        Vec::new()
    };

    Ok(Pictogram {
        id,
        profile,
        title,
        description,
        verb,
        direction,
        actors,
        assemblies,
        declared_deviations,
    })
}

fn parse_metadata(node: Node<'_, '_>) -> Result<(String, String), String> {
    check_attributes(node, &[])?;
    let children = element_children(node);
    if children.len() != 2 {
        return Err("metadata requires title followed by description".to_string());
    }
    expect_element(children[0], "title", DSL_NS)?;
    expect_element(children[1], "description", DSL_NS)?;
    check_attributes(children[0], &[])?;
    check_attributes(children[1], &[])?;
    let title = required_text(children[0], "title")?;
    let description = required_text(children[1], "description")?;
    Ok((title, description))
}

fn parse_intent(node: Node<'_, '_>) -> Result<(String, String), String> {
    check_attributes(node, &["verb", "direction"])?;
    ensure_empty(node)?;
    let verb = required_attr(node, "verb")?.to_string();
    validate_identifier(&verb, "intent verb")?;
    let direction = node
        .attribute("direction")
        .unwrap_or("stationary")
        .to_string();
    if !["left", "right", "up", "down", "stationary"].contains(&direction.as_str()) {
        return Err(format!("unsupported intent direction {direction:?}"));
    }
    Ok((verb, direction))
}

fn parse_scene(node: Node<'_, '_>) -> Result<(Vec<Actor>, Vec<Assembly>), String> {
    check_attributes(node, &[])?;
    let children = element_children(node);
    if children.is_empty() {
        return Err("scene must contain at least one actor or assembly".to_string());
    }
    let mut actors = Vec::new();
    let mut assemblies = Vec::new();
    let mut ids = BTreeSet::new();
    for child in children {
        match child.tag_name().name() {
            "actor" => {
                expect_namespace(child, DSL_NS)?;
                let actor = parse_actor(child)?;
                if !ids.insert(actor.id.clone()) {
                    return Err(format!("duplicate scene id {:?}", actor.id));
                }
                actors.push(actor);
            }
            "assembly" => {
                expect_namespace(child, DSL_NS)?;
                let assembly = parse_assembly(child)?;
                if !ids.insert(assembly.id.clone()) {
                    return Err(format!("duplicate scene id {:?}", assembly.id));
                }
                assemblies.push(assembly);
            }
            other => return Err(format!("unsupported scene element {other:?}")),
        }
    }
    Ok((actors, assemblies))
}

fn parse_actor(node: Node<'_, '_>) -> Result<Actor, String> {
    check_attributes(node, &["id", "facing"])?;
    let id = required_attr(node, "id")?.to_string();
    validate_identifier(&id, "actor id")?;
    let facing = required_attr(node, "facing")?.to_string();
    if !["left", "right", "front"].contains(&facing.as_str()) {
        return Err(format!("actor {id} has unsupported facing {facing:?}"));
    }
    let children = element_children(node);
    if children.len() != 2 {
        return Err(format!("actor {id} requires head followed by pose"));
    }
    expect_element(children[0], "head", DSL_NS)?;
    expect_element(children[1], "pose", DSL_NS)?;
    let head = parse_xy(children[0])?;

    check_attributes(children[1], &[])?;
    let joint_nodes = element_children(children[1]);
    if joint_nodes.is_empty() {
        return Err(format!("actor {id} pose is empty"));
    }
    let mut joints = HashMap::new();
    for joint in joint_nodes {
        expect_element(joint, "joint", DSL_NS)?;
        check_attributes(joint, &["name", "x", "y"])?;
        let name = required_attr(joint, "name")?.to_string();
        let point = parse_xy(joint)?;
        if joints.insert(name.clone(), point).is_some() {
            return Err(format!("actor {id} repeats joint {name}"));
        }
    }
    Ok(Actor {
        id,
        facing,
        head,
        joints,
    })
}

fn parse_assembly(node: Node<'_, '_>) -> Result<Assembly, String> {
    check_attributes(node, &["id", "role", "layer", "color-role"])?;
    let id = required_attr(node, "id")?.to_string();
    validate_identifier(&id, "assembly id")?;
    let role = required_attr(node, "role")?.to_string();
    if !["prop", "subject"].contains(&role.as_str()) {
        return Err(format!("assembly {id} has unsupported role {role:?}"));
    }
    let layer = required_attr(node, "layer")?.to_string();
    let color_role = node.attribute("color-role").unwrap_or("figure").to_string();
    let children = element_children(node);
    if children.is_empty() {
        return Err(format!("assembly {id} has no primitives"));
    }
    let mut primitives = Vec::new();
    for child in children {
        expect_namespace(child, DSL_NS)?;
        let primitive = match child.tag_name().name() {
            "bar" => {
                check_attributes(child, &["x1", "y1", "x2", "y2"])?;
                ensure_empty(child)?;
                Primitive::Bar {
                    start: parse_point_attrs(child, "x1", "y1")?,
                    end: parse_point_attrs(child, "x2", "y2")?,
                }
            }
            "disc" | "ring" => {
                check_attributes(child, &["cx", "cy", "radius"])?;
                ensure_empty(child)?;
                let center = parse_point_attrs(child, "cx", "cy")?;
                let radius = parse_i32_attr(child, "radius")?;
                if child.tag_name().name() == "disc" {
                    Primitive::Disc { center, radius }
                } else {
                    Primitive::Ring { center, radius }
                }
            }
            "box" => {
                check_attributes(child, &["x", "y", "width", "height"])?;
                ensure_empty(child)?;
                Primitive::Box {
                    origin: parse_xy(child)?,
                    width: parse_i32_attr(child, "width")?,
                    height: parse_i32_attr(child, "height")?,
                }
            }
            "wedge" => {
                check_attributes(child, &["x1", "y1", "x2", "y2", "x3", "y3"])?;
                ensure_empty(child)?;
                Primitive::Wedge {
                    points: [
                        parse_point_attrs(child, "x1", "y1")?,
                        parse_point_attrs(child, "x2", "y2")?,
                        parse_point_attrs(child, "x3", "y3")?,
                    ],
                }
            }
            other => {
                return Err(format!(
                    "assembly {id} uses unsupported primitive {other:?}"
                ));
            }
        };
        primitives.push(primitive);
    }
    Ok(Assembly {
        id,
        role,
        layer,
        color_role,
        primitives,
    })
}

fn parse_expression(node: Node<'_, '_>) -> Result<Vec<Deviation>, String> {
    check_attributes(node, &[])?;
    let children = element_children(node);
    if children.is_empty() {
        return Err("expression must contain at least one deviation".to_string());
    }
    let mut deviations = Vec::new();
    for child in children {
        expect_element(child, "deviation", DSL_NS)?;
        check_attributes(child, &["feature", "target", "cost", "reason"])?;
        ensure_empty(child)?;
        let feature = required_attr(child, "feature")?.to_string();
        let target = required_attr(child, "target")?.to_string();
        let cost = parse_u32_attr(child, "cost")?;
        let reason = required_attr(child, "reason")?.trim();
        if reason.is_empty() {
            return Err(format!("deviation {feature}:{target} needs a reason"));
        }
        deviations.push(Deviation {
            feature,
            target,
            cost,
        });
    }
    Ok(deviations)
}

fn parse_canon(source: &str) -> Result<Canon, String> {
    let options = ParsingOptions {
        allow_dtd: false,
        ..ParsingOptions::default()
    };
    let document = Document::parse_with_options(source, options)
        .map_err(|error| format!("invalid canon XML: {error}"))?;
    let root = document.root_element();
    expect_element(root, "canon", CANON_NS)?;
    let id = required_attr(root, "id")?.to_string();

    let canvas = one_child(root, "canvas", CANON_NS)?;
    let width = parse_i32_attr(canvas, "width")?;
    let height = parse_i32_attr(canvas, "height")?;
    let grid_step = parse_i32_attr(canvas, "grid-step")?;
    let safe_margin = parse_i32_attr(canvas, "safe-margin")?;

    let geometry = one_child(root, "geometry", CANON_NS)?;
    let head_radius = parse_i32_attr(geometry, "head-radius")?;
    let body_width = parse_f64_attr(geometry, "body-width")?;
    let equipment_width = parse_f64_attr(geometry, "equipment-width")?;

    let palette_node = one_child(root, "palette", CANON_NS)?;
    let mut palette = HashMap::new();
    for role in element_children(palette_node) {
        expect_element(role, "role", CANON_NS)?;
        palette.insert(
            required_attr(role, "id")?.to_string(),
            required_attr(role, "value")?.to_string(),
        );
    }

    let directions_node = one_child(root, "directions", CANON_NS)?;
    let mut directions = HashMap::new();
    for vector in element_children(directions_node) {
        expect_element(vector, "vector", CANON_NS)?;
        directions.insert(
            (parse_i32_attr(vector, "dx")?, parse_i32_attr(vector, "dy")?),
            parse_u32_attr(vector, "cost")?,
        );
    }

    let anatomy = one_child(root, "anatomy", CANON_NS)?;
    let mut bones = Vec::new();
    for bone in element_children(anatomy) {
        expect_element(bone, "bone", CANON_NS)?;
        bones.push(Bone {
            role: required_attr(bone, "role")?.to_string(),
            from: required_attr(bone, "from")?.to_string(),
            to: required_attr(bone, "to")?.to_string(),
            min_length: parse_f64_attr(bone, "min-length")?,
            max_length: parse_f64_attr(bone, "max-length")?,
            layer: required_attr(bone, "layer")?.to_string(),
        });
    }

    let layers_node = one_child(root, "layers", CANON_NS)?;
    let mut ordered_layers = Vec::new();
    for layer in element_children(layers_node) {
        expect_element(layer, "layer", CANON_NS)?;
        ordered_layers.push((
            parse_i32_attr(layer, "order")?,
            required_attr(layer, "id")?.to_string(),
        ));
    }
    ordered_layers.sort_by_key(|item| item.0);
    let layers = ordered_layers.into_iter().map(|item| item.1).collect();

    let limits = one_child(root, "limits", CANON_NS)?;
    Ok(Canon {
        id,
        width,
        height,
        grid_step,
        safe_margin,
        head_radius,
        body_width,
        equipment_width,
        palette,
        directions,
        bones,
        layers,
        max_actors: parse_usize_attr(limits, "max-actors")?,
        max_assemblies: parse_usize_attr(limits, "max-assemblies")?,
        max_primitives: parse_usize_attr(limits, "max-primitives-per-assembly")?,
        max_expression_cost: parse_u32_attr(limits, "max-expression-cost")?,
    })
}

fn validate_points(
    target: &str,
    points: &[Point],
    canon: &Canon,
    safe: bool,
    errors: &mut Vec<String>,
    derived: &mut BTreeSet<Deviation>,
) {
    let margin = if safe { canon.safe_margin } else { 0 };
    if points.iter().any(|point| {
        point.x < margin
            || point.y < margin
            || point.x > canon.width - margin
            || point.y > canon.height - margin
    }) {
        errors.push(format!(
            "{target} has coordinates outside the {}",
            if safe { "safe area" } else { "canvas" }
        ));
    }
    if points
        .iter()
        .any(|point| point.x % canon.grid_step != 0 || point.y % canon.grid_step != 0)
    {
        derived.insert(Deviation {
            feature: "half-grid".to_string(),
            target: target.to_string(),
            cost: 1,
        });
    }
}

fn validate_declarations(
    declared: &[Deviation],
    derived: &BTreeSet<Deviation>,
    max_cost: u32,
    errors: &mut Vec<String>,
) {
    let mut declared_set = BTreeSet::new();
    for item in declared {
        if !declared_set.insert(item.clone()) {
            errors.push(format!(
                "duplicate deviation declaration {}:{}",
                item.feature, item.target
            ));
        }
    }
    for item in derived.difference(&declared_set) {
        errors.push(format!(
            "missing deviation: feature={} target={} cost={}",
            item.feature, item.target, item.cost
        ));
    }
    for item in declared_set.difference(derived) {
        errors.push(format!(
            "undeclared geometry does not require deviation: feature={} target={} cost={}",
            item.feature, item.target, item.cost
        ));
    }
    let cost: u32 = derived.iter().map(|item| item.cost).sum();
    if cost > max_cost {
        errors.push(format!(
            "expression cost {cost} exceeds profile maximum {max_cost}"
        ));
    }
}

fn compile_svg(validated: &Validated) -> String {
    let canon = &validated.canon;
    let pictogram = &validated.pictogram;
    let mut normal: BTreeMap<(String, String), Vec<String>> = BTreeMap::new();
    let mut rings: BTreeMap<(String, String), Vec<String>> = BTreeMap::new();

    for actor in &pictogram.actors {
        for bone in &canon.bones {
            let start = actor.joints[&bone.from];
            let end = actor.joints[&bone.to];
            normal
                .entry((bone.layer.clone(), "figure".to_string()))
                .or_default()
                .push(segment_path(start, end, canon.body_width));
        }
        normal
            .entry(("head".to_string(), "figure".to_string()))
            .or_default()
            .push(circle_path(actor.head, canon.head_radius as f64));
    }

    for assembly in &pictogram.assemblies {
        let key = (assembly.layer.clone(), assembly.color_role.clone());
        for primitive in &assembly.primitives {
            match primitive {
                Primitive::Bar { start, end } => normal
                    .entry(key.clone())
                    .or_default()
                    .push(segment_path(*start, *end, canon.equipment_width)),
                Primitive::Disc { center, radius } => normal
                    .entry(key.clone())
                    .or_default()
                    .push(circle_path(*center, *radius as f64)),
                Primitive::Ring { center, radius } => rings
                    .entry(key.clone())
                    .or_default()
                    .push(ring_path(*center, *radius as f64, canon.equipment_width)),
                Primitive::Box {
                    origin,
                    width,
                    height,
                } => normal.entry(key.clone()).or_default().push(format!(
                    "M {} {} H {} V {} H {} Z",
                    origin.x,
                    origin.y,
                    origin.x + width,
                    origin.y + height,
                    origin.x
                )),
                Primitive::Wedge { points } => normal
                    .entry(key.clone())
                    .or_default()
                    .push(polygon_path(points)),
            }
        }
    }

    let mut body = String::new();
    let mut id_counts: HashMap<String, usize> = HashMap::new();
    for layer in &canon.layers {
        let mut roles: Vec<_> = normal
            .keys()
            .chain(rings.keys())
            .filter(|(candidate, _)| candidate == layer)
            .map(|(_, role)| role.clone())
            .collect();
        roles.sort();
        roles.dedup();
        for role in roles {
            let color = &canon.palette[&role];
            let base_id = format!("{}-{}", sanitize_id(layer), sanitize_id(&role));
            if let Some(paths) = normal.get(&(layer.clone(), role.clone())) {
                let id = unique_id(&base_id, &mut id_counts);
                body.push_str(&format!(
                    "  <path id=\"{}\" fill=\"{}\" d=\"{}\"/>\n",
                    id,
                    xml_escape(color),
                    paths.join(" ")
                ));
            }
            if let Some(paths) = rings.get(&(layer.clone(), role.clone())) {
                for path in paths {
                    let id = unique_id(&format!("{base_id}-ring"), &mut id_counts);
                    body.push_str(&format!(
                        "  <path id=\"{}\" fill=\"{}\" fill-rule=\"evenodd\" d=\"{}\"/>\n",
                        id,
                        xml_escape(color),
                        path
                    ));
                }
            }
        }
    }

    let facing = pictogram
        .actors
        .iter()
        .map(|actor| actor.facing.as_str())
        .collect::<Vec<_>>()
        .join(",");
    format!(
        "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 {} {}\" role=\"img\" aria-labelledby=\"title desc\" data-profile=\"{}\" data-intent=\"{}\" data-direction=\"{}\" data-facing=\"{}\">\n  <title id=\"title\">{}</title>\n  <desc id=\"desc\">{}</desc>\n{}</svg>\n",
        canon.width,
        canon.height,
        xml_escape(&canon.id),
        xml_escape(&pictogram.verb),
        xml_escape(&pictogram.direction),
        xml_escape(&facing),
        xml_escape(&pictogram.title),
        xml_escape(&pictogram.description),
        body
    )
}

fn segment_path(start: Point, end: Point, width: f64) -> String {
    let dx = (end.x - start.x) as f64;
    let dy = (end.y - start.y) as f64;
    let length = (dx * dx + dy * dy).sqrt();
    let px = -dy / length * width / 2.0;
    let py = dx / length * width / 2.0;
    let points = [
        (start.x as f64 + px, start.y as f64 + py),
        (end.x as f64 + px, end.y as f64 + py),
        (end.x as f64 - px, end.y as f64 - py),
        (start.x as f64 - px, start.y as f64 - py),
    ];
    float_polygon_path(&points)
}

fn polygon_path(points: &[Point]) -> String {
    let points: Vec<_> = points
        .iter()
        .map(|point| (point.x as f64, point.y as f64))
        .collect();
    float_polygon_path(&points)
}

fn float_polygon_path(points: &[(f64, f64)]) -> String {
    let mut output = format!(
        "M {} {}",
        format_number(points[0].0),
        format_number(points[0].1)
    );
    for point in &points[1..] {
        output.push_str(&format!(
            " L {} {}",
            format_number(point.0),
            format_number(point.1)
        ));
    }
    output.push_str(" Z");
    output
}

fn circle_path(center: Point, radius: f64) -> String {
    let left = center.x as f64 - radius;
    let right = center.x as f64 + radius;
    format!(
        "M {} {} A {} {} 0 1 0 {} {} A {} {} 0 1 0 {} {} Z",
        format_number(left),
        center.y,
        format_number(radius),
        format_number(radius),
        format_number(right),
        center.y,
        format_number(radius),
        format_number(radius),
        format_number(left),
        center.y
    )
}

fn ring_path(center: Point, radius: f64, width: f64) -> String {
    let inner = (radius - width).max(0.5);
    format!(
        "{} {}",
        circle_path(center, radius),
        circle_path(center, inner)
    )
}

fn write_output(path: &Path, contents: &str) -> Result<(), String> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|error| format!("cannot create {}: {error}", parent.display()))?;
    }
    fs::write(path, contents).map_err(|error| format!("cannot write {}: {error}", path.display()))
}

fn one_child<'a, 'input>(
    parent: Node<'a, 'input>,
    name: &str,
    namespace: &str,
) -> Result<Node<'a, 'input>, String> {
    let matches: Vec<_> = element_children(parent)
        .into_iter()
        .filter(|node| {
            node.tag_name().name() == name && node.tag_name().namespace() == Some(namespace)
        })
        .collect();
    if matches.len() != 1 {
        return Err(format!("expected exactly one {name} element"));
    }
    Ok(matches[0])
}

fn element_children<'a, 'input>(node: Node<'a, 'input>) -> Vec<Node<'a, 'input>> {
    node.children().filter(Node::is_element).collect()
}

fn expect_element(node: Node<'_, '_>, name: &str, namespace: &str) -> Result<(), String> {
    if node.tag_name().name() != name || node.tag_name().namespace() != Some(namespace) {
        return Err(format!(
            "expected {{{namespace}}}{name}, found {{{}}}{}",
            node.tag_name().namespace().unwrap_or(""),
            node.tag_name().name()
        ));
    }
    Ok(())
}

fn expect_namespace(node: Node<'_, '_>, namespace: &str) -> Result<(), String> {
    if node.tag_name().namespace() != Some(namespace) {
        return Err(format!(
            "element {} uses the wrong namespace",
            node.tag_name().name()
        ));
    }
    Ok(())
}

fn check_attributes(node: Node<'_, '_>, allowed: &[&str]) -> Result<(), String> {
    for attribute in node.attributes() {
        if !allowed.contains(&attribute.name()) {
            return Err(format!(
                "element {} has unsupported attribute {}",
                node.tag_name().name(),
                attribute.name()
            ));
        }
    }
    Ok(())
}

fn required_attr<'a, 'input>(node: Node<'a, 'input>, name: &str) -> Result<&'a str, String> {
    node.attribute(name).ok_or_else(|| {
        format!(
            "element {} requires attribute {name}",
            node.tag_name().name()
        )
    })
}

fn parse_xy(node: Node<'_, '_>) -> Result<Point, String> {
    parse_point_attrs(node, "x", "y")
}

fn parse_point_attrs(node: Node<'_, '_>, x: &str, y: &str) -> Result<Point, String> {
    Ok(Point {
        x: parse_i32_attr(node, x)?,
        y: parse_i32_attr(node, y)?,
    })
}

fn parse_i32_attr(node: Node<'_, '_>, name: &str) -> Result<i32, String> {
    required_attr(node, name)?.parse().map_err(|_| {
        format!(
            "attribute {name} on {} must be an integer",
            node.tag_name().name()
        )
    })
}

fn parse_u32_attr(node: Node<'_, '_>, name: &str) -> Result<u32, String> {
    required_attr(node, name)?.parse().map_err(|_| {
        format!(
            "attribute {name} on {} must be a non-negative integer",
            node.tag_name().name()
        )
    })
}

fn parse_usize_attr(node: Node<'_, '_>, name: &str) -> Result<usize, String> {
    required_attr(node, name)?.parse().map_err(|_| {
        format!(
            "attribute {name} on {} must be a non-negative integer",
            node.tag_name().name()
        )
    })
}

fn parse_f64_attr(node: Node<'_, '_>, name: &str) -> Result<f64, String> {
    required_attr(node, name)?.parse().map_err(|_| {
        format!(
            "attribute {name} on {} must be numeric",
            node.tag_name().name()
        )
    })
}

fn ensure_empty(node: Node<'_, '_>) -> Result<(), String> {
    if node
        .children()
        .any(|child| child.is_element() || child.text().is_some_and(|text| !text.trim().is_empty()))
    {
        return Err(format!("element {} must be empty", node.tag_name().name()));
    }
    Ok(())
}

fn required_text(node: Node<'_, '_>, label: &str) -> Result<String, String> {
    if node.children().any(|child| child.is_element()) {
        return Err(format!("{label} cannot contain elements"));
    }
    let value = node.text().unwrap_or("").trim();
    if value.is_empty() {
        return Err(format!("{label} cannot be empty"));
    }
    Ok(value.to_string())
}

fn validate_identifier(value: &str, label: &str) -> Result<(), String> {
    let mut chars = value.chars();
    let Some(first) = chars.next() else {
        return Err(format!("{label} cannot be empty"));
    };
    if !(first.is_ascii_alphabetic() || first == '_')
        || chars.any(|character| {
            !(character.is_ascii_alphanumeric()
                || character == '-'
                || character == '_'
                || character == '.')
        })
    {
        return Err(format!("{label} {value:?} is not a valid XML name"));
    }
    Ok(())
}

fn gcd(mut a: i32, mut b: i32) -> i32 {
    if a == 0 {
        return b.max(1);
    }
    if b == 0 {
        return a.max(1);
    }
    while b != 0 {
        let remainder = a % b;
        a = b;
        b = remainder;
    }
    a.max(1)
}

fn distance(a: Point, b: Point) -> f64 {
    let dx = (a.x - b.x) as f64;
    let dy = (a.y - b.y) as f64;
    (dx * dx + dy * dy).sqrt()
}

fn display_list(values: &[&str]) -> String {
    if values.is_empty() {
        "none".to_string()
    } else {
        values.join(", ")
    }
}

fn format_number(value: f64) -> String {
    let rounded = format!("{value:.3}");
    rounded
        .trim_end_matches('0')
        .trim_end_matches('.')
        .to_string()
}

fn xml_escape(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

fn sanitize_id(value: &str) -> String {
    value
        .chars()
        .map(|character| {
            if character.is_ascii_alphanumeric() || character == '-' || character == '_' {
                character
            } else {
                '-'
            }
        })
        .collect()
}

fn unique_id(base: &str, counts: &mut HashMap<String, usize>) -> String {
    let count = counts.entry(base.to_string()).or_insert(0);
    *count += 1;
    if *count == 1 {
        base.to_string()
    } else {
        format!("{base}-{}", *count)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const EXAMPLE: &str = include_str!("../references/jumping-jacks.pictogram.xml");
    const CANON: &str = include_str!("../canon/aicher-inspired-48-v1.xml");

    #[test]
    fn validates_bundled_example() {
        let result = validate_document(EXAMPLE, CANON).expect("example should validate");
        assert!(result.deviations.is_empty());
        assert_eq!(result.pictogram.verb, "jumping-jacks");
        assert_eq!(result.pictogram.direction, "stationary");
        assert_eq!(result.pictogram.actors[0].facing, "front");
    }

    #[test]
    fn compiles_deterministically() {
        let result = validate_document(EXAMPLE, CANON).expect("example should validate");
        let first = compile_svg(&result);
        let second = compile_svg(&result);
        assert_eq!(first, second);
        assert!(first.contains("viewBox=\"0 0 48 48\""));
        assert!(!first.contains("<script"));
        assert!(!first.contains("transform="));
    }

    #[test]
    fn rejects_dtds() {
        let source = EXAMPLE.replacen(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            "<?xml version=\"1.0\"?><!DOCTYPE pictogram [<!ENTITY x \"bad\">]>",
            1,
        );
        assert!(validate_document(&source, CANON).is_err());
    }

    #[test]
    fn supports_best_effort_subject_assemblies() {
        let source = r#"
<p:pictogram xmlns:p="urn:labs:pictogram:1"
             id="bird"
             profile="aicher-inspired-48-v1">
  <p:metadata>
    <p:title>Bird</p:title>
    <p:description>A reduced bird in flight.</p:description>
  </p:metadata>
  <p:intent verb="fly" direction="right"/>
  <p:scene>
    <p:assembly id="bird" role="subject" layer="torso" color-role="accent">
      <p:disc cx="24" cy="24" radius="4"/>
      <p:wedge x1="20" y1="24" x2="10" y2="16" x3="18" y3="28"/>
      <p:wedge x1="28" y1="24" x2="38" y2="16" x3="30" y3="28"/>
    </p:assembly>
  </p:scene>
  <p:expression>
    <p:deviation feature="custom-assembly"
                 target="bird"
                 cost="1"
                 reason="The subject does not use human anatomy."/>
  </p:expression>
</p:pictogram>
"#;
        let result = validate_document(source, CANON).expect("assembly should validate");
        assert_eq!(result.deviations.len(), 1);
        assert!(compile_svg(&result).contains("#5BA6C9"));
    }
}
