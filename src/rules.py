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
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from pandac.PandaModules import *
import board
import piece,chessAI
import sys
import copy

WHITE = (1,1,1,1)
BLACK = (0.2,0.2,0.2,1)
HIGHLIGHT = (0, 1, 1, 1)

def labelLegalPawnMove(boardGame):
	result = []
	(x,y,z) = boardGame.currLabel
	# Check if it's the first move
	if not boardGame.currPiece.firstMove:
		availMove = 2
	else:
		availMove = 1
	if boardGame.currPiece.color == WHITE:
		dX = 1
	else:
		dX = -1
	if y == 0:
		for dZ in range(8):
			if boardGame.pieceList[x][y+1][dZ] != None:
				continue
			result.append((x,y+1,dZ))
	if y == 5:
		for dZ in range(8):
			if boardGame.pieceList[x][y-1][dZ] != None:
				continue
			result.append((x,y-1,dZ))
	# Check if the move is legal
	for dZ in range(8):
		for i in range(availMove):
			if boardGame.pieceList[x+dX*(i+1)][y][dZ] != None:
				break
			else:
				result.append((x+dX*(i+1),y,dZ))
	for move in [-1,+1]:
		for dZ in range(8):
			if y+move >= 0 and y+move < 6:
				if (boardGame.pieceList[x+dX][y+move][dZ] != None and 
					int(boardGame.pieceList[x+dX][y+move][dZ].colorR) != boardGame.currPlayer):
					result.append((x+dX,y+move,dZ))
	return result

def labelLegalBishopMove(boardGame):
	result = []
	(x,y,z) = boardGame.currLabel
	for dZ in range(1,8):
		# Moves on the diagonal
		for move in [(-1,-1),(+1,-1),(-1,+1),(+1,+1)]:
			for i in range(1,6):
				dX = i*move[0]
				dY = i*move[1]
				if inLegalRange(x+dX,y+dY,dZ):
					if boardGame.pieceList[x+dX][y+dY][dZ] != None:
						# Check if we can remove a piece
				 		if int(boardGame.pieceList[x+dX][y+dY][dZ].colorR) != boardGame.currPlayer:
				 			result.append((x+dX,y+dY,dZ))
						break
					result.append((x+dX,y+dY,dZ))
	return result

def labelLegalRookMove(boardGame):
	result = []
	(x,y,z) = boardGame.currLabel
	for dZ in range(-2,+3):
		# Moves on straight lines
		for move in [(-1,0),(+1,0),(0,+1),(0,+1)]:
			for i in range(1,6):
				dX = i*move[0]
				dY = i*move[1]
				# Check if the move is legal
				if inLegalRange(x+dX,y+dY,z+dZ):
					if boardGame.pieceList[x+dX][y+dY][z+dZ] != None:
				 		if int(boardGame.pieceList[x+dX][y+dY][z+dZ].colorR) != boardGame.currPlayer:
				 			result.append((x+dX,y+dY,z+dZ))
						break
				result.append((x+dX,y+dY,z+dZ))
	return result

def labelLegalKingMove(boardGame):
	result = []
	(x,y,z) = boardGame.currLabel
	for dZ in range(-2,+3):
		# Move one step at a time
		for move in [(-1,0),(+1,0),(0,+1),(0,+1),(-1,-1),(+1,-1),(-1,+1),(+1,+1)]:
			dX = move[0]
			dY = move[1]
			# Check if the move is legal
			if inLegalRange(x+dX,y+dY,z+dZ):
				if boardGame.pieceList[x+dX][y+dY][z+dZ] != None:
					if int(boardGame.pieceList[x+dX][y+dY][z+dZ].colorR) != boardGame.currPlayer:
						result.append((x+dX,y+dY,z+dZ))
					continue
				result.append((x+dX,y+dY,z+dZ))
	return result

def labelLegalQueenMove(boardGame):
	result = []
	(x,y,z) = boardGame.currLabel
	for dZ in range(8):
		for move in [(-1,0),(+1,0),(0,+1),(0,+1),(-1,-1),(+1,-1),(-1,+1),(+1,+1)]:
			for i in range(1,6):
				dX = i*move[0]
				dY = i*move[1]
				# Check if the move is legal
				if inLegalRange(x+dX,y+dY,dZ):
					if boardGame.pieceList[x+dX][y+dY][dZ] != None:
				 		if int(boardGame.pieceList[x+dX][y+dY][dZ].colorR) != boardGame.currPlayer:
				 			result.append((x+dX,y+dY,dZ))
						break
					result.append((x+dX,y+dY,dZ))
	return result

def labelLegalKnightMove(boardGame):
	result = []
	(x,y,z) = boardGame.currLabel
	for dZ in range(-2,+3):
		for move in [(-2,-1),(-2,+1),(+2,-1),(+2,+1),(-1,-2),(+1,-2),(-1,+2),(+1,+2)]:
			dX = move[0]
			dY = move[1]
			# Check if the move is legal
			if inLegalRange(x+dX,y+dY,z+dZ):
				if boardGame.pieceList[x+dX][y+dY][z+dZ] != None:
					if int(boardGame.pieceList[x+dX][y+dY][z+dZ].colorR) != boardGame.currPlayer:
						result.append((x+dX,y+dY,z+dZ))
					continue
				result.append((x+dX,y+dY,z+dZ))
	return result

def inLegalRange(x,y,z):
	if x<0 or x>9:
		return False
	if y<0 or y>5:
		return False
	if z<0 or z>7:
		return False
	return True

def labelLegalMove(boardGame):
	if boardGame.currPiece == None:
		return []
	result = []
	if boardGame.currPiece.getType() == "models/pawn":
		result = labelLegalPawnMove(boardGame)
	if boardGame.currPiece.getType() == "models/bishop":
		result = labelLegalBishopMove(boardGame)
	if boardGame.currPiece.getType() == "models/rook":
		result = labelLegalRookMove(boardGame)
	if boardGame.currPiece.getType() == "models/king":
		result = labelLegalKingMove(boardGame)
	if boardGame.currPiece.getType() == "models/queen":
		result = labelLegalQueenMove(boardGame)
	if boardGame.currPiece.getType() == "models/knight":
		result = labelLegalKnightMove(boardGame)
	newResult = []
	for posi in result:
		(x,y,z) = posi
		if inLegalRange(x,y,z):
			if boardGame.board.board[x][y][z] != False:
				if boardGame.pieceList[x][y][z] == None:
					newResult.append(posi)
				elif (boardGame.pieceList[x][y][z] != None and 
					int(boardGame.pieceList[x][y][z].colorR) != boardGame.currPlayer):
					newResult.append(posi)

	return newResult

def checkMate(boardGame):
	otherPlayer = 1-boardGame.currPlayer
	# Locate the king
	for x in range(len(boardGame.board.board)):
		for y in range(len(boardGame.board.board[0])):
			for z in range(len(boardGame.board.board[0][0])):
				if (boardGame.pieceList[x][y][z] != None and
					boardGame.pieceList[x][y][z].model.split("/")[1] == "king" and
					int(boardGame.pieceList[x][y][z].colorR) == otherPlayer):
					currKing = (x,y,z)
	(x,y,z) = currKing
	tempAI = chessAI.ChessAI(boardGame)
	possibleMoveDict = tempAI.getMoves()
	# Check if the king is in threat
	for posi in possibleMoveDict:
		(pX,pY,pZ) = posi
		if int(boardGame.pieceList[pX][pY][pZ].colorR) != boardGame.currPlayer:
			continue
		if (x,y,z) in possibleMoveDict[posi]:
			return True
	return False

def makeMove(board, oldPosi, newPosi):
	(x,y,z) = oldPosi
	piece = board[x][y][z]
	board[x][y][z] = None
	(x,y,z) = newPosi
	board[x][y][z] = piece

def labelLegalBoard(boardGame):
	(x,y,z) = boardGame.currLabel
	legalList = []
	dList = [(1,1,2),(1,4,2),(4,1,2),(4,4,2),(3,1,4),(3,4,4),(6,1,4),(6,4,4),(5,1,6),(5,4,6),(8,1,6),(8,4,6)]
	for (dX,dY,dZ) in dList:
		if abs(dY-y) <= 1 and boardGame.board.board[dX][dY][dZ+1] == False:
			legalList.append((dX, dY, dZ))
	return legalList