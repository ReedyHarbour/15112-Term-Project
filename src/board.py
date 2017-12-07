from math import pi, sin, cos
 
from direct.showbase.ShowBase import ShowBase
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
from panda3d.core import AmbientLight, DirectionalLight, LightAttrib
from panda3d.core import TextNode
from panda3d.core import LPoint3, LVector3, BitMask32
from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from pandac.PandaModules import *
import sys,rules

WHITE = (1,1,1,1)
BLACK = (0,0,0,1)

# Get current square default color
def getColor(row,col,level):
	if (row+col)%2 == 0:
		return BLACK
	return WHITE

class ChessBoard(object):
	def __init__(self, dx, dy, dz, boardGame):
		self.square = boardGame.square
		self.piece = boardGame.piece
		# Set up board as a 3D list
		self.board = [[[False]*8 for i in range(6)] for j in range(10)]
		self.rows = 10
		self.cols = 6
		self.level = 8
		for level in range(8):
			self.initBoard(level)
		for row in range(self.rows):
			for col in range(self.cols):
				for level in range(self.level):
					if self.board[row][col][level]: 
						color = getColor(row,col,level)
						self.board[row][col][level] = Square(row, col, level, dx, dy, dz, self.square, color)

	def initBoard(self, level):
		if level == 2 or level == 4 or level == 6:
			for row in range(level-1, level+3):
				for col in range(1,5):
					self.board[row][col][level] = True
		if level == 3:
			trueList = [(0,0),(0,1),(1,0),(1,1),(0,4),(0,5),(1,4),(1,5)]
			for (row,col) in trueList:
				self.board[row][col][level] = True
		if level == 7:
			trueList = [(8,0),(9,0),(8,1),(9,1),(8,4),(8,5),(9,4),(9,5)]
			for (row,col) in trueList:
				self.board[row][col][level] = True

	def getSquare(self,row,col,level):
		return self.board[row][col][level]

	def addOn(self, model, row, col, level, dz):
		assert(isinstance(self, ChessBoard))
		square = self.getSquare(row,col,level)
		assert(isinstance(square,Square))
		x = square.getX()
		y = square.getY()
		z = square.getZ()
		return AddOn(model, x+0.5, y+0.5, z+dz, self.piece)

	def addPiece(self, model, row, col, level, color):
		square = self.getSquare(row, col, level)
		assert(isinstance(square,Square))
		x = square.getX()
		y = square.getY()
		z = square.getZ()
		return Piece(model,x,y,z,color,self.piece)

class Square(object):
	def __init__(self, pX, pY, pZ, dx, dy, dz, square, color):
		self.square = loader.loadModel("models/square")
		self.square.reparentTo(square)
		self.color = color
		self.square.setColor(color)
		self.square.setPos(LPoint3(pX+dx, pY+dy, pZ+dz))
		self.setLabel(pX, pY, pZ)

	# Cited from https://www.panda3d.org/manual/index.php/Sample_Programs:_Chessboard
	def setLabel(self, pX, pY, pZ):
		self.square.find("**/polygon").node().setIntoCollideMask(
				BitMask32.bit(1))
		self.square.find("**/polygon").node().setTag('square', "%d,%d,%d" %(pX,pY,pZ))

	def getX(self):
		return self.square.getX()
	def getY(self):
		return self.square.getY()
	def getZ(self):
		return self.square.getZ()

	def setColor(self,color):
		self.square.setColor(color)

class AddOn(object):
	def __init__(self, model, pX, pY, pZ, renderNode):
		self.addon = loader.loadModel(model)
		self.addon.reparentTo(renderNode)
		self.addon.setColor(VBase4(0.2, 0.2, 0.2, 1))
		self.addon.setScale(.5)
		self.addon.setPos(LPoint3(pX,pY,pZ))
		self.pX = pX-0.5
		self.pY = pY-0.5
		self.pZ = pZ-0.5

	def getPosi(self):
		return (self.pX, self.pY, self.pZ)

	def setPosi(self, pX, pY, pZ):
		self.addon.setPos(LPoint3(pX+0.5,pY+0.5,pZ+0.5))

class Piece(object):
	def __init__(self, model, pX, pY, pZ, color, renderNode):
		self.obj = loader.loadModel(model)
		self.model = model
		self.obj.reparentTo(renderNode)
		self.obj.setColor(color)
		self.obj.setPos(LPoint3(pX,pY,pZ))
		self.firstMove = False
		self.color = color
		self.colorR = color[0]

	def getType(self):
		return self.model

	def getMove(self, x, y, z, board):
		temp = board.currLabel
		board.currLabel = (x,y,z)
		possibleMove = rules.labelLegalKingMove(board)
		board.currLabel = temp
		return possibleMove
