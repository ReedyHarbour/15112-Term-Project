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
import board
import sys,copy

WHITE = (1,1,1,1)
BLACK = (0.2, 0.2, 0.2, 1)

def initializePieces(boardGame):

	boardGame.pieceList = [[[None]*8 for i in range(6)] for j in range(10)]
	# Put pieces onto the board
	boardGame.pieceList[0][4][3] = boardGame.board.addPiece("models/king",0,4,3,WHITE)
	boardGame.pieceList[0][1][3] = boardGame.board.addPiece("models/queen",0,1,3,WHITE)
	boardGame.pieceList[0][0][3] = boardGame.board.addPiece("models/rook",0,0,3,WHITE)
	boardGame.pieceList[0][5][3] = boardGame.board.addPiece("models/rook",0,5,3,WHITE)
	boardGame.pieceList[1][2][2] = boardGame.board.addPiece("models/bishop",1,2,2,WHITE)
	boardGame.pieceList[1][3][2] = boardGame.board.addPiece("models/bishop",1,3,2,WHITE)
	boardGame.pieceList[1][1][2] = boardGame.board.addPiece("models/knight",1,1,2,WHITE)
	boardGame.pieceList[1][4][2] = boardGame.board.addPiece("models/knight",1,4,2,WHITE)
	boardGame.pieceList[1][1][2].obj.setHpr(-90,0,0)
	boardGame.pieceList[1][4][2].obj.setHpr(-90,0,0)

	boardGame.pieceList[9][1][7] = boardGame.board.addPiece("models/king",9,1,7,BLACK)
	boardGame.pieceList[9][4][7] = boardGame.board.addPiece("models/queen",9,4,7,BLACK)
	boardGame.pieceList[9][0][7] = boardGame.board.addPiece("models/rook",9,0,7,BLACK)
	boardGame.pieceList[9][5][7] = boardGame.board.addPiece("models/rook",9,5,7,BLACK)
	boardGame.pieceList[8][2][6] = boardGame.board.addPiece("models/bishop",8,2,6,BLACK)
	boardGame.pieceList[8][3][6] = boardGame.board.addPiece("models/bishop",8,3,6,BLACK)
	boardGame.pieceList[8][1][6] = boardGame.board.addPiece("models/knight",8,1,6,BLACK)
	boardGame.pieceList[8][4][6] = boardGame.board.addPiece("models/knight",8,4,6,BLACK)
	boardGame.pieceList[8][1][6].obj.setHpr(90,0,0)
	boardGame.pieceList[8][4][6].obj.setHpr(90,0,0)

	# Put pawns onto the board
	initializeWhite(boardGame, WHITE)
	initializeBlack(boardGame, BLACK)

def initializeWhite(boardGame, color):
	listOfPawns = [(1,0,3),(1,1,3),(1,4,3),(1,5,3),(2,1,2),(2,2,2),(2,3,2),(2,4,2)]
	for (row,col,level) in listOfPawns:
		boardGame.pieceList[row][col][level] = boardGame.board.addPiece("models/pawn",row,col,level,color)

def initializeBlack(boardGame, color):
	listOfPawns = [(8,0,7),(8,1,7),(8,4,7),(8,5,7),(7,1,6),(7,2,6),(7,3,6),(7,4,6)]
	for (row,col,level) in listOfPawns:
		boardGame.pieceList[row][col][level] = boardGame.board.addPiece("models/pawn",row,col,level,color)
