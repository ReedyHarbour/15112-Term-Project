from math import pi, sin, cos
import math

from direct.showbase.ShowBase import ShowBase
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
from panda3d.core import AmbientLight, DirectionalLight, LightAttrib
from panda3d.core import Light, Spotlight
from panda3d.core import TextNode
from panda3d.core import LPoint3, LVector3, BitMask32
from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.DirectGuiBase import DGG
from direct.task.Task import Task
from direct.actor.Actor import Actor
from pandac.PandaModules import *
import board,piece,rules
import sys
import copy
import random

class ChessAI(object):
	def __init__(self, game, maxDepth=4):
		self.maxDepth = maxDepth
		# ChessGame object
		self.game = game
		self.bestBlackMove = None
		self.bestWhiteMove = None
		self.currLabel = None
		self.currPlayer = self.game.currPlayer
		# Sets value for each piece type
		self.valueList = {"king":900,
						  "queen":500,
						  "rook":300,
						  "bishop":300,
						  "knight":300,
						  "pawn":100}

	# Return a dictionary keys are piece positions and values are lists of legal moves
	def getMoves(self):
		pieceList = []
		pieceLabel = []
		possibleMove = dict()
		boardGame = self.game
		for x in range(len(boardGame.board.board)):
			for y in range(len(boardGame.board.board[0])):
				for z in range(len(boardGame.board.board[0][0])):
					if boardGame.pieceList[x][y][z] != None:
						pieceLabel.append((x,y,z))
						pieceList.append(boardGame.pieceList[x][y][z])
		for i in range(len(pieceList)):
			boardGame.currPiece = pieceList[i]
			boardGame.currLabel = pieceLabel[i]
			possibleMove[boardGame.currLabel] = rules.labelLegalMove(boardGame)
		return possibleMove

	# Update the piece in list
	def makeMove(self, board, oldPosi, newPosi):
		(x,y,z) = oldPosi
		piece = board[x][y][z]
		board[x][y][z] = None
		(x,y,z) = newPosi
		board[x][y][z] = piece

	# Return the entir board value by adding current pieces
	def getBoardValue(self, board):
		value = 0
		for x in range(len(board)):
			for y in range(len(board[0])):
				for z in range(len(board[0][0])):
					if board[x][y][z] != None:
						piece = board[x][y][z]
						if int(piece.colorR) == 0:
							color = -1
						else:
							color = 1
						value += color*self.valueList[piece.model.split("/")[1]]
		return value

	# Evaluation data modified from https://chessprogramming.wikispaces.com/Simplified+evaluation+function
	def getKnightPosiValue(self,x,y,z):
		return -5*(abs(x-5)+abs(y-3)+abs(z-4))+20

	def getBishopPosiValue(self,x,y,z):
		return -5*(abs(x-5)+abs(y-3)+abs(z-4))+20

	def getRookPosiValue(self,x,y,z):
		if x == 7:
			if y == 1 or y == 4:
				return 5
			return 10
		if y == 1 or y == 4:
			return -5
		return 0

	def getPawnPosiValue(self,x,y,z,color):
		if color == 0:
			return -2*abs(y-3)-5*x
		else:
			return -2*abs(y-3)+5*x

	def getQueenPosiValue(self,x,y,z):
		return -5*(abs(x-5)+abs(y-3)+abs(z-4))+20

	def getKingPosiValue(self,x,y,z,color):
		if color == 0:
			if x < 7:
				return 5*(x-7)+abs(y-3)-10
			else:
				return 5*(7-x)-abs(y-3)+10
		else:
			if x > 2:
				return -5*(x-2)+abs(y-3)-10
			else:
				return 5*(2-x)+abs(y-3)+10

	# Return each position value corresponding to the piece on it
	def getPosiValue(self, board):
		(x,y,z) = self.currLabel
		if board[x][y][z] != None:
			label = board[x][y][z].model.split("/")[1]
			color = int(board[x][y][z].colorR)
			if color == 0:
				scalar = -1
			else:
				scalar = 1
			if label == "knight":
				return scalar*self.getKnightPosiValue(x,y,z)
			if label == "bishop":
				return scalar*self.getBishopPosiValue(x,y,z)
			if label == "rook":
				return scalar*self.getRookPosiValue(x,y,z)
			if label == "pawn":
				return self.getPawnPosiValue(x,y,z,color)
			if label == "queen":
				return scalar*self.getQueenPosiValue(x,y,z)
			if label == "king":
				return self.getKingPosiValue(x,y,z,color)
		return 0

	# Modified from https://en.wikipedia.org/wiki/Alpha%E2%80%93beta_pruning#Pseudocode
	def alphabeta(self, board, alpha, beta, depth=1):
		if depth == 3:
			# Evaluate
			boardValue = self.getBoardValue(board)
			boardValue += self.getPosiValue(board)
			return boardValue
		if depth % 2 == 0:
			# Black's move, find min player's turn
			bestValue = float("inf")
			possibleMove = self.getMoves()
			for oldPosi in possibleMove:
				(x,y,z) = oldPosi
				if int(self.game.pieceList[x][y][z].colorR) != 0:
					continue
				for newPosi in possibleMove[oldPosi]:
					# Generate a node board
					experimentBoard = copy.deepcopy(board)
					self.makeMove(experimentBoard, oldPosi, newPosi)
					self.currLabel = newPosi
					value = self.alphabeta(experimentBoard, alpha, beta, depth+1)
					if value < bestValue:
						bestValue = value
						self.bestBlackMove = (oldPosi,newPosi)
					if value == bestValue:
						flip = random.randint(0,1)
						if flip == 1:
							bestValue = value
							self.bestBlackMove = (oldPosi,newPosi)
					beta = min(beta, bestValue)
					if alpha >= beta:
						break
			return bestValue
		else:
			# White's move, find max player's turn
			bestValue = float("-inf")
			possibleMove = self.getMoves()
			for oldPosi in possibleMove:
				(x,y,z) = oldPosi
				if int(self.game.pieceList[x][y][z].colorR) != 1:
					continue
				for newPosi in possibleMove[oldPosi]:
					# Generate a node board
					self.currLabel = oldPosi
					experimentBoard = copy.deepcopy(board)
					self.makeMove(experimentBoard, oldPosi, newPosi)
					value = self.alphabeta(experimentBoard, alpha, beta, depth+1)
					if value > bestValue:
						bestValue = value
						self.bestWhiteMove = (oldPosi,newPosi)
					if value == bestValue:
						flip = random.randint(0,1)
						if flip == 1:
							bestValue = value
							self.bestWhiteMove = (oldPosi,newPosi)
					alpha = max(alpha, bestValue)
					if alpha >= beta:
						break
			return bestValue
		return 0

	def move(self):
		experimentBoard = copy.deepcopy(self.game.pieceList)
		self.bestMove = None
		if self.game.currPlayer == 1:
			bestValue = self.alphabeta(experimentBoard, float("-inf"), float("inf"))
			return self.bestWhiteMove
		else:
			bestValue = self.alphabeta(experimentBoard, float("-inf"), float("inf"), depth=0)
			return self.bestBlackMove
