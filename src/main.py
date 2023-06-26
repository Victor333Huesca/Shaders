from pathlib import Path, WindowsPath
import sys
from time import time
from typing import Optional as Opt, cast, overload

import numpy as np
from OpenGL import GL

from PyQt6.QtGui import QKeyEvent, QSurfaceFormat, QResizeEvent, QWheelEvent
from PyQt6.QtOpenGL import QOpenGLWindow, QOpenGLVersionProfile
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSize, QTimer, Qt

from OpenGL.GL.shaders import compileProgram, compileShader, ShaderProgram, ShaderCompilationError, ShaderValidationError, ShaderLinkError


vertex_shader   = Path(__file__).parent / 'shaders' / 'vertex.vert'
fragment_shader = Path(__file__).parent / 'shaders' / 'fragment.frag'


class OpenGLWindow(QOpenGLWindow):
  def __init__(self):
    super().__init__()
    self.shader: Opt[ShaderProgram] = None

    self.iResolution = (0, 0)
    self.iFactor: float = 8
    self.iTime: float = 0
    self._start_time = time()

    timer = QTimer(self)
    timer.timeout.connect(self.tick)
    timer.start(1000//75)

  @staticmethod
  def compileShader(src_or_path: str | Path, shader_type: GL.GL_FRAGMENT_SHADER | GL.GL_VERTEX_SHADER):
    # 0. Get source
    src: str = {
      WindowsPath: WindowsPath.read_text,
      Path:        Path.read_text,
      str:         lambda x: x,
    }[type(src_or_path)](src_or_path)

    # 1. Compile shaders
    return compileShader(src, shader_type)

  @classmethod
  def compileShaderProgram(cls):
    # 1. Compile shaders
    shaders = [cls.compileShader(vertex_shader,   GL.GL_VERTEX_SHADER),
               cls.compileShader(fragment_shader, GL.GL_FRAGMENT_SHADER)]

    # 2. Compile program
    return compileProgram(*shaders)

  class Buffer: ...

  @overload
  @staticmethod
  def createBuffer(target: GL.GL_ARRAY_BUFFER, data: list[float]) -> Buffer: ...
  @overload
  @staticmethod
  def createBuffer(target: GL.GL_ELEMENT_ARRAY_BUFFER, data: list[int]) -> Buffer: ...
  @staticmethod
  def createBuffer(target: GL.GL_ARRAY_BUFFER | GL.GL_ELEMENT_ARRAY_BUFFER, data: list[float] | list[int]) -> Buffer:
    dtype = {
      GL.GL_ARRAY_BUFFER:         np.float32,
      GL.GL_ELEMENT_ARRAY_BUFFER: np.uint32
    }[target]
    packed_data = np.array(data, dtype=dtype)
    buffer = GL.glGenBuffers(1)
    GL.glBindBuffer(target, buffer)
    GL.glBufferData(target, packed_data.nbytes, packed_data, GL.GL_STATIC_DRAW)
    return buffer

  def findUniform(self, name: str):
    loc = GL.glGetUniformLocation(self.shader, name)
    if loc < 0:
      raise ValueError(f'error ({loc}): couldn\'t find uniform "{name}"')
    return loc

  def initializeGL(self):
    prof = QOpenGLVersionProfile()
    prof.setVersion(3, 3)
    prof.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    # self.ctx = self.context()
    # self.fmt = self.format()
    # self.fmt.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)

    print(f'Open GL version: {cast(bytes, GL.glGetString(GL.GL_VERSION)).decode()}')

    # Debug
    # GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)

    # 0. Compile and use shader
    self.recompile()
    if self.shader is None:
      print('error: unable to initialize shader, exit.')
      exit(-1)

    # 1. Attach the Vertex Array Object
    self.vao = GL.glGenVertexArrays(1)
    GL.glBindVertexArray(self.vao)

    # 2. Copy vertices in the Vertex Buffer Object
    factor = 1
    self.vbo = self.createBuffer(GL.GL_ARRAY_BUFFER, [factor * v for v in [-1., -1.,   -1., 1.,   1., 1.,   1., -1.]])

    # 3. Copy indices in an element buffer object
    self.ebo = self.createBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, [0, 1, 2,   2, 3, 0])

    # 4. Map attributes
    GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
    GL.glEnableVertexAttribArray(0)

  def paintGL(self):
    # 0. Clear
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    if self.shader is None:
      return

    # 1. Use shader and vao
    GL.glUseProgram(self.shader)
    GL.glBindVertexArray(self.vao)

    # 2. Update uniforms
    GL.glUniform2uiv(self.findUniform('iResolution'), 1, np.array(self.iResolution, dtype=np.uint32))
    GL.glUniform1f(self.findUniform('iFactor'), np.array([self.iFactor], dtype=np.float32))
    GL.glUniform1f(self.findUniform('iTime'), np.array([self.iTime], dtype=np.float32))

    # 3. Draw
    GL.glDrawElements(GL.GL_TRIANGLES, 6, GL.GL_UNSIGNED_INT, None)

  def wheelEvent(self, e: QWheelEvent):
    super().wheelEvent(e)
    self.iFactor *= 1 + ((e.angleDelta().y() // 120) * .1)
    self.iFactor = max(self.iFactor, 0.1)
    self.update()

  def resizeEvent(self, event: QResizeEvent):
    super().resizeEvent(event)
    self.iResolution = self.size().width(), self.size().height()
    self.update()

  def tick(self):
    self.iTime = time() - self._start_time
    # print(f'tick: {self.iTime:.2f}')
    self.update()

  def keyReleaseEvent(self, e: QKeyEvent):
    super().keyReleaseEvent(e)
    if e.key() == Qt.Key.Key_A:
      self.recompile()

  def recompile(self):
    shader = None
    try:
      shader = self.compileShaderProgram()
    except ShaderCompilationError as e:
      err, source, shader_type = cast(tuple[str, list[bytes], GL.GL_FRAGMENT_SHADER | GL.GL_VERTEX_SHADER], e.args)
      err_t, err_msg = err.split(': ', 1)
      print(err_t)
      print(eval(err_msg).decode())
      if False:
        print('-----')
        for line in source:
          print(line.decode())
        print('-----')
        print(shader_type)
    except ShaderValidationError as e:
      print(e)
    except ShaderLinkError as e:
      print(e)
    else:
      GL.glUseProgram(shader)
    finally:
      self.shader = shader


def main():
  app = QApplication(sys.argv)
  GLwindow = OpenGLWindow()
  GLwindow.resize(QSize(800, 800))
  GLwindow.show()
  app.exec()


if __name__ == '__main__':
  main()
