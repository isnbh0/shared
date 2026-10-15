# Shaders and 3D

GPU rendering gives code control over geometry, perspective, texture sampling, lighting, and effects. A 3D scene is usually defined as objects and a camera, and a renderer projects it into a two-dimensional frame. Shaders are programmable stages inside that process. [WebGPU rendering pipeline](https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API), [three.js scene basics](https://threejs.org/manual/pages/creating-a-scene.html).

## The path from geometry to pixels

A mesh is made of geometry and a material. The geometry supplies positions and other per-vertex data. A vertex shader transforms the vertex positions, including the projection through a camera. The triangles are then rasterized into the pixel locations they cover, and a fragment shader calculates the color at each of those locations, often from textures, lighting inputs, and geometry data interpolated across the triangle. WebGPU exposes these stages as a render pipeline, and WebGL exposes related shader programs and drawing state through a canvas context. [WebGPU pipeline](https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API), [WebGL API](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API), [three.js materials](https://threejs.org/manual/pages/materials.html).

The same model works for more than literal 3D objects. A full-screen rectangle can run a fragment shader over every pixel to produce gradients, noise, distortions, procedural patterns, or transitions. A shader can treat an image as a texture and transform its coordinates or colors. A render target can hold the output of one pass as a texture for a later pass. [three.js render targets](https://threejs.org/manual/pages/rendertargets.html), [WebGPU textures and pipelines](https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API).

## Scene graph, camera, and material

A **scene graph** organizes objects as parents and children. Each object has a local coordinate system, and moving a parent also moves its children. That keeps compound motion manageable: a camera rig can move as one unit, and a wheel can spin inside a moving vehicle. A 3D scene graph can contain meshes, groups, lights, and cameras. [three.js scene graph](https://threejs.org/manual/pages/scenegraph.html).

The camera decides which part of the scene appears in the frame and how depth maps onto the image. With a perspective camera, objects get smaller with distance. An orthographic camera keeps scale constant with depth, which also makes it useful for 2D-like arrangements. Moving the camera is animation in its own right: changing its position, orientation, zoom, or projection turns a fixed scene into a new shot. [three.js cameras](https://threejs.org/manual/pages/cameras.html).

Materials decide how surfaces are drawn. Some are unlit, and others respond to lights. Textures can hold surface color, normals, roughness, or other data. Shape and appearance are kept apart, so you can restyle an object without remodeling its geometry. [three.js materials](https://threejs.org/manual/pages/materials.html), [three.js fundamentals](https://threejs.org/manual/pages/fundamentals.html).

## Effects as passes

An offscreen **render target** is a texture that the renderer draws into. A later pass can sample that texture to add blur, glow, depth effects, color treatment, or compositing, or to combine a 3D shot with a 2D graphic. Several passes in a row form an effects chain, and each pass may need its own texture format, dimensions, and clear behavior. [three.js render targets](https://threejs.org/manual/pages/rendertargets.html), [RenderTarget API](https://threejs.org/docs/pages/RenderTarget.html).

WebGPU also has **compute pipelines**, which process data in parallel and need not draw to a canvas. They can generate or update buffers and textures that a later render pass uses. Compute produces scene data or effects, and the rendered video frame still comes from sampling the finished image. [WebGPU API](https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API).

## Renderer choices and output fidelity

WebGL is widely available in modern browsers and exposes GPU-backed 2D/3D rendering through a canvas. WebGPU adds an explicit model of devices, command encoders, resources, render pipelines, and compute pipelines, and you must check its availability and the device limits. A library such as three.js supplies higher-level objects and renderer methods on top of these APIs. [WebGL API](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API), [WebGPU API](https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API), [three.js renderer](https://threejs.org/docs/pages/WebGLRenderer.html).

The current three.js `WebGPURenderer` can use WebGPU when it is available and fall back to WebGL 2. Its material and post-processing model differs from that of `WebGLRenderer`, so custom `ShaderMaterial` and `EffectComposer` setups have to be adapted. A project's existing effects therefore influence the choice of renderer. [three.js WebGPURenderer manual](https://threejs.org/manual/pages/webgpurenderer).

The renderer's logical size, drawing-buffer size, and pixel ratio can differ, and the sharpness of the delivered frame depends on the buffer actually sampled for export. Color is another choice in the pipeline. three.js distinguishes nonlinear sRGB values, used for images and output, from the linear values used in lighting calculations, and render targets can play different color-space roles. A mismatch may change how an encoded frame looks even when the geometry is correct. [three.js renderer sizing](https://threejs.org/docs/pages/WebGLRenderer.html), [three.js color management](https://threejs.org/manual/pages/color-management.html).

Capturing GPU output can mean reading pixels from a render target or capturing the canvas as an image or a stream. `WebGLRenderer` provides pixel readback methods for render targets, and browser capture methods have their own timing and origin restrictions. [three.js renderer API](https://threejs.org/docs/pages/WebGLRenderer.html), [canvas captureStream](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/captureStream). See [Deterministic rendering](Deterministic%20rendering.md) for time and export, and [Representation models](Representation%20models.md) for how 3D can combine with other graphics.
