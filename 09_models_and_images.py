import math
import os
import sys
import struct  

import glm
import moderngl
import pygame
import pywavefront
from PIL import Image

os.environ['SDL_WINDOWS_DPI_AWARENESS'] = 'permonitorv2'

pygame.init()
pygame.display.set_mode((800, 800), flags=pygame.OPENGL | pygame.DOUBLEBUF, vsync=True)


class ImageTexture:
    def __init__(self, path):
        self.ctx = moderngl.get_context()
        img = Image.open(path).convert('RGBA')
        self.texture = self.ctx.texture(img.size, 4, img.tobytes())
        self.texture.use()  
        self.texture.build_mipmaps()  
        self.texture.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)

    def use(self):
        self.texture.use()


class ModelGeometry:
    def __init__(self, path):
        self.ctx = moderngl.get_context()
        
        
        obj = pywavefront.Wavefront(path, collect_faces=True)
        
        vertices = []
        for name, mesh in obj.meshes.items():
            for face in mesh.faces:
                for vertex_i in face:
                    vertex = obj.vertices[vertex_i]
                    vertices.extend(vertex[:3])  
                    if len(vertex) >= 5:  
                        vertices.extend(vertex[3:5])  

       
        vertex_data = struct.pack(f'{len(vertices)}f', *vertices)
        
       
        self.vbo = self.ctx.buffer(data=vertex_data)

    def vertex_array(self, program):
      
        return self.ctx.vertex_array(program, [(self.vbo, '3f 2f', 'in_vertex', 'in_uv')])


class Mesh:
    def __init__(self, program, geometry, texture=None):
        self.ctx = moderngl.get_context()
        self.vao = geometry.vertex_array(program)
        self.texture = texture

    def render(self, position, color, scale):
        self.vao.program['use_texture'].value = self.texture is not None

        if self.texture:
            self.texture.use()

        self.vao.program['position'] = position
        self.vao.program['color'] = color
        self.vao.program['scale'] = scale
        self.vao.render()


class Scene:
    def __init__(self):
        self.ctx = moderngl.get_context()

        self.program = self.ctx.program(
            vertex_shader='''
                #version 330 core

                uniform mat4 camera;
                uniform vec3 position;
                uniform float scale;

                layout (location = 0) in vec3 in_vertex;
                layout (location = 1) in vec2 in_uv;

                out vec3 v_vertex;
                out vec2 v_uv;

                void main() {
                    v_vertex = position + in_vertex * scale;
                    v_uv = in_uv;

                    gl_Position = camera * vec4(v_vertex, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330 core

                uniform sampler2D Texture;
                uniform bool use_texture;
                uniform vec3 color;

                in vec3 v_vertex;
                in vec2 v_uv;

                layout (location = 0) out vec4 out_color;

                void main() {
                    if (use_texture) {
                        out_color = texture(Texture, v_uv) * vec4(color, 1.0);
                    } else {
                        out_color = vec4(color, 1.0);
                    }
                }
            ''',
        )

        self.texture = ImageTexture('examples/data/textures/TECLOGO.png')

    
        self.skull_geometry = ModelGeometry('examples/data/models/12140_Skull_v3_L2.obj')
        self.skull = Mesh(self.program, self.skull_geometry)

        self.cat_geometry = ModelGeometry('examples/data/models/12221_Cat_v1_l3.obj')
        self.cat = Mesh(self.program, self.cat_geometry, self.texture)

    def camera_matrix(self):
       
        eye = (0.0, 0.0, 7.0) 
        proj = glm.perspective(45.0, 1.0, 0.1, 1000.0)
        look = glm.lookAt(eye, (0.0, 0.0, 0.0), (0.0, 1.0, 0.0))
        return proj * look

    def render(self):
        camera = self.camera_matrix()

        self.ctx.clear()
        self.ctx.enable(self.ctx.DEPTH_TEST)

        self.program['camera'].write(camera)

        
        self.skull.render((0.0, 0.0, -1.0), (1.0, 0.5, 0.5), 0.1)  
        self.cat.render((0.0, 0.0, 0.0), (0.7, 0.7, 1.0), 0.1)   


scene = Scene()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    scene.render()

    pygame.display.flip()
