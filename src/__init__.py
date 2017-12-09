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
from panda3d.core import TransparencyAttrib
from direct.gui.DirectGuiBase import DGG
from direct.task.Task import Task
from direct.actor.Actor import Actor
from pandac.PandaModules import *
import board,piece,rules,chessAI,button
import sys
import copy

WHITE = (1,1,1,1)
BLACK = (0,0,0,1)
HIGHLIGHT = (0, 1, 1, 1)
HIGHLIGHT2 = (0, 0.5, 1, 1)
HIGHLIGHT3 = (0,0.5,0.5,1)

def ChangeColor(color):
	if color == WHITE:
		return BLACK
	return WHITE

def getColor(x,y):
	if (x+y)%2 == 1:
		return BLACK
	return WHITE

class ChessGame(ShowBase):
	# Make a move automatically after player makes a move
	def onePlayerGame(self):
		self.mode = 1
		self.initButton()
		self.setUp()
	
	def twoPlayerGame(self):
		self.mode = 2
		self.initButton()
		self.setUp()

	def setUp(self):
		self.counted = 0
		# Hide init screen
		self.initFrame.hide()
		self.playFrame.show()
		self.currPlayer = 0 # BLACK
		self.AI = chessAI.ChessAI(self)
		self.setBackgroundColor(0.9, 0.89, 0.9, 1)
		self.printList = []
		self.printStr = []

		# Cited from https://www.panda3d.org/forums/viewtopic.php?t=5595
		# Put background behind models
		self.background = OnscreenImage(parent=render2dp, image="image/gameBG.png", scale=(2,1,1))
		base.cam2dp.node().getDisplayRegion(0).setSort(-20)

		self.camera.setPosHpr(0, -13, 8, 0, -35, 0)
		self.currSquare = None
		self.currSquareColor = None
		self.currPiece = None
		self.currLabel = None
		self.prevLabel = None
		self.prevPiece = None
		self.prevPossMove = []
		self.possibleMove = []
		self.removedBlackList = []
		self.removedWhiteList = []
		self.moveList = []
		self.undoList = []
		self.moved = False
		self.count = 0
		self.currBoard = None
		self.prevBoard = None
		self.setupLights()

		self.mousePosition = None
		self.isReset = False
		self.heading = 0
		self.pitch = -35
		self.roll = 0
		self.boardMove = False
		self.keyMap = dict()

		# Cited from https://www.panda3d.org/manual/index.php/Clicking_on_3D_Objects
		self.cTrav = CollisionTraverser()
		self.collHandler = CollisionHandlerQueue()
		self.pickerNode = CollisionNode('mouseRay')
		self.pickerNP = self.camera.attachNewNode(self.pickerNode)
		self.pickerNode.setFromCollideMask(BitMask32.bit(1))
		self.pickerRay = CollisionRay()
		self.pickerNode.addSolid(self.pickerRay)
		self.cTrav.addCollider(self.pickerNP, self.collHandler)

		self.square = render.attachNewNode("squareRoot")
		self.piece = render.attachNewNode("chessPiece")
		self.removed = render.attachNewNode("removed")

		# Initialize the chess board
		self.board = board.ChessBoard(-6,-2,-6,self)
		self.oriBoard = copy.deepcopy(self.board.board)

		# Initialize all the pieces
		piece.initializePieces(self)
		
		# Initialize supporting cylinders
		addon = "models/cylinder"
		self.addOnList = []
		self.addOnList.append(self.board.addOn(addon,0,0,3,-.5))
		self.addOnList.append(self.board.addOn(addon,8,0,7,-.5))
		self.addOnList.append(self.board.addOn(addon,0,4,3,-.5))
		self.addOnList.append(self.board.addOn(addon,8,4,7,-.5))
		self.SUPPORT1 = self.board.addOn("models/support",4,2,4,-1)
		self.SUPPORT2 = self.board.addOn("models/support",6,2,6,-1)
		
		self.lookAt = render.attachNewNode("player")
		self.lookAt.setPos(0,0,-1)
		self.camera.lookAt(self.lookAt)

		# Set accepted key presses and mouse presses
		self.accept("mouse1", self.click)
		self.accept("mouse1-up", self.clickRelease)
		self.accept("wheel_up", self.setKey, ["wheel_up", 1])
		self.accept("wheel_down", self.setKey, ["wheel_down", 1])

		self.keyMap["wheel_up"] = 0
		self.keyMap["wheel_down"] = 0
		for key in ['arrow_left', 'arrow_right', 'arrow_up', 'arrow_down', 'a', 'd', 'w', 's']:
			self.keyMap[key] = 0
			self.accept(key, self.setKey, [key, 1])
			self.accept('%s-up' % key, self.setKey, [key, 0])

		self.taskMgr.add(self.mouseTask, 'mouseTask')
		self.taskMgr.add(self.keyControlCamera, 'controlCamera')

		self.cameraNode = render.attachNewNode("camera")
		self.camera.reparentTo(self.cameraNode)

	def exit(self):
		sys.exit()

	# Set up tutorial screen
	def tutorial(self):
		self.tutorialFrame.destroy()
		self.tutorialFrame = DirectFrame(frameColor=(1,1,1,0),
					  frameSize=(-3,3,-2,2), pos=(0, -1, 0))
		self.tutorialImage = OnscreenImage(image='image/tutorial%s.png' % self.currTutorial, pos=(0,1,0), 
							  scale = (1.9,1,1), parent=self.tutorialFrame)
		tutorialButton = button.TutorialButton(self)
		self.initFrame.hide()
		self.playFrame.hide()
		self.endFrame.hide()

	def moveToNextTutorial(self):
		self.currTutorial += 1
		self.currTutorial %= 6
		self.tutorial()

	def restartScreen(self):
		self.initFrame.show()
		self.playFrame.hide()
		self.tutorialFrame.hide()
		self.endFrame.hide()
		try: 
			self.square.hide()
			self.piece.hide()
			self.removed.hide()
			self.player.destroy()
		except: pass
		render.clearLight()
		self.mode = 0

	def restartGame(self):
		self.playFrame.hide()
		self.endFrame.hide()
		self.drawWinner.destroy()
		self.player.destroy()
		try:
			render.clearLight()
			self.square.hide()
			self.piece.hide()
			self.removed.hide()
			if self.mode == -1:
				self.playFrame.show()
				self.onePlayerGame()
			if self.mode == -2:
				self.playFrame.show()
				self.twoPlayerGame()
		except:
			pass

	def resumeScreen(self):
		if self.mode > 0:
			self.playFrame.show()
			self.initFrame.hide()
		else:
			self.playFrame.hide()
			self.initFrame.show()
		self.tutorialFrame.hide()

	def initScreen(self):
		self.font = loader.loadFont('AvenirLTStd-Light.otf')
		self.camera.setPosHpr(0, -5, 0, 0, 0, 0)
		button.InitButton(self)
		self.currTutorial = 0
		# Initialize frames
		self.playFrame = DirectFrame(frameColor=(1,1,1,0),
					  frameSize=(-3,3,-2,2), pos=(0, -1, 0))
		self.endFrame = DirectFrame(frameColor=(1,1,1,0),
					  frameSize=(-3,3,-2,2), pos=(0, -1, 0))
		self.tutorialFrame = DirectFrame(frameColor=(1,1,1,0),
					  frameSize=(-3,3,-2,2), pos=(0, -1, 0))

		# Initialize end game frame
		background = OnscreenImage(image='image/endGame.png', pos=(0,0,0), scale = (2,1,1), parent=self.endFrame)
		background.setTransparency(TransparencyAttrib.MBinary)
		self.mainMenu = DirectButton(pos=(0, 0, -.14), text="Main Menu", 
								   text_fg=(.2,.2,.2,1), command=self.restartScreen, 
								   text_font=self.font, parent=self.endFrame,
								   scale=.07, pad=(.4, .2), frameColor=(0.7,0.3,0.2,0),
								   relief=DGG.FLAT)
		self.restart = DirectButton(pos=(0, 0, -.32), text="Try Again", 
								   text_fg=(.2,.2,.2,1), command=self.restartGame, 
								   text_font=self.font, parent=self.endFrame,
								   scale=.07, pad=(.4, .2), frameColor=(0.7,0.3,0.2,0),
								   relief=DGG.FLAT)
		self.endFrame.hide()
		self.tutorialImage = OnscreenImage(image='image/tutorial%s.png' % self.currTutorial, pos=(0,1,0), 
							  scale = (1.9,1,1), parent=self.tutorialFrame)
		tutorialButton = button.TutorialButton(self)
		self.tutorialFrame.hide()

	def initButton(self):
		button.PlayButton(self)

	def __init__(self):
		ShowBase.__init__(self)
		self.disableMouse()
		self.initScreen()
		self.mode = 0

	def setKey(self, key, value):
		self.keyMap[key] = value

##############################################
# Camera Control Functions
##############################################

	def setKeyUp(self):
		if self.changeView['text'] == "Rotate":
			self.camera.setZ(self.camera, .6)
			self.camera.lookAt(self.lookAt)
		else:
			self.camera.setZ(self.camera, -.6)

	def setKeyDown(self):
		if self.changeView['text'] == "Rotate":
			self.camera.setZ(self.camera, -.6)
			self.camera.lookAt(self.lookAt)
		else:
			self.camera.setZ(self.camera, .6)

	def setKeyLeft(self):
		if self.changeView['text'] == "Rotate":
			a = -.16
			x = self.camera.getX()
			y = self.camera.getY()
			w1 = x*cos(a) - y*sin(a)
			w2 = x*sin(a) + y*cos(a)
			self.camera.setPos(w1, w2, self.camera.getZ())
			self.camera.lookAt(self.lookAt)
		else:
			self.camera.setX(self.camera, .6)

	def setKeyRight(self):
		if self.changeView['text'] == "Rotate":
			a = .16
			x = self.camera.getX()
			y = self.camera.getY()
			w1 = x*cos(a) - y*sin(a)
			w2 = x*sin(a) + y*cos(a)
			self.camera.setPos(w1, w2, self.camera.getZ())
			self.camera.lookAt(self.lookAt)
		else:
			self.camera.setX(self.camera, -.6)

	def keyControlCamera(self, task):
		dt = globalClock.getDt()

		a = dt*3*-self.keyMap['arrow_left'] + dt*3*self.keyMap['arrow_right']                    
		if a != 0:
			x = self.camera.getX()
			y = self.camera.getY()
			w1 = x*cos(a) - y*sin(a)
			w2 = x*sin(a) + y*cos(a)
			self.camera.setPos(w1, w2, self.camera.getZ())
			self.camera.lookAt(self.lookAt)
		if self.keyMap['arrow_up'] != 0 or self.keyMap['arrow_down'] != 0:
			self.camera.setZ(self.camera, dt*10*self.keyMap['arrow_up'] +
					   dt*10*-self.keyMap['arrow_down'])
			self.camera.lookAt(self.lookAt)

		if self.keyMap['s'] != 0 or self.keyMap['w'] != 0:
			self.camera.setZ(self.camera, dt*10*self.keyMap['s'] + dt*10*-self.keyMap['w'])
		
		self.camera.setX(self.camera, dt*10*self.keyMap['a'] + dt*10*-self.keyMap['d'])
		self.camera.setY(self.camera, dt*10*self.keyMap['wheel_up'] + dt*10*-self.keyMap['wheel_down'])
		self.keyMap['wheel_up'] = 0
		self.keyMap['wheel_down'] = 0

		return Task.cont

	def resetView(self):
		self.camera.setPosHpr(0, -13, 8, 0, -35, 0)

	def changeCameraView(self):
		if self.changeView['text'] == "Rotate":
			self.changeView['text'] = "Zoom"
		else:
			self.changeView['text'] = "Rotate"

	# Change board button lookings
	def setBoard(self):
		if self.boardMove:
			self.boardMove = False
			self.currPiece = None
			self.prevPiece = None
			self.prevLabel = None
			self.possibleMove = []
			self.prevPossMove = []
			self.boardButton["text_fg"] = (0.2,0.2,0.2,1)
		else:
			self.boardMove = True
			self.boardButton["text_fg"] = (0.5,0.5,0.7,1)

##############################################
# Board control functions
##############################################

	def movePiece(self):
		if self.currLabel not in self.prevPossMove:
			return
		(pX,pY,pZ) = self.prevLabel
		self.pieceList[pX][pY][pZ] = None
		(x,y,z) = self.currLabel
		# Display the moved piece
		self.prevPiece.obj.setPos(LPoint3(x-6,y-2,z-6))
		self.moveList.append((self.prevLabel,self.currLabel))
		self.prevPiece.firstMove = True
		self.pieceList[x][y][z] = self.prevPiece
		self.currPiece = None
		self.currPlayer = 1-self.currPlayer
		self.undoList = []

	def undoMoveOnce(self):
		if len(self.moveList) != 0:
			(prevPosi, currPosi) = self.moveList.pop()
			self.undoList.append((prevPosi, currPosi))
			(x,y,z) = currPosi
			movePiece = self.pieceList[x][y][z]
			self.pieceList[x][y][z] = None
			(pX,pY,pZ) = prevPosi
			self.pieceList[pX][pY][pZ] = movePiece
			movePiece.obj.setPos(LPoint3(pX-6,pY-2,pZ-6))
			# Check if the last move removed a piece
			if len(self.removedBlackList) != 0:
				(piece,posi) = self.removedBlackList[-1]
				if posi == (x,y,z):
					self.pieceList[x][y][z] = self.removedBlackList[-1][0]
					self.removedBlackList[-1][0].obj.setPos(LPoint3(x-6,y-2,z-6))
					self.removedBlackList.pop()
					piece.obj.reparentTo(self.piece)
			if len(self.removedWhiteList) != 0:
				(wPiece,wPosi) = self.removedWhiteList[-1]
				if wPosi == (x,y,z):
					self.pieceList[x][y][z] = self.removedWhiteList[-1][0]
					self.removedWhiteList[-1][0].obj.setPos(LPoint3(x-6,y-2,z-6))
					self.removedWhiteList.pop()
					wPiece.obj.reparentTo(self.piece)
			if abs(x-pX) == 2:
				movePiece.firstMove = False
			self.currPlayer = 1-self.currPlayer
		else:
			self.printList.append("No previous move!")

	def undoMove(self):
		if self.mode == 1:
			# Undo both white and black moves
			self.undoMoveOnce()
			self.undoMoveOnce()
		else:
			self.undoMoveOnce()

	def redoMove(self):
		if len(self.undoList) != 0:
			(prevPosi, currPosi) = self.undoList.pop()
			self.moveList.append((prevPosi, currPosi))
			(x,y,z) = prevPosi
			movePiece = self.pieceList[x][y][z]
			self.pieceList[x][y][z] = None
			(pX,pY,pZ) = currPosi
			if self.pieceList[pX][pY][pZ] != None:
				removedPiece = self.pieceList[pX][pY][pZ]
				# Check the removed piece's color
				if int(removedPiece.colorR) == 0:
					self.removedBlackList.append((removedPiece,currPosi))
				else:
					self.removedWhiteList.append((removedPiece,currPosi))
				(rX,rY,rZ) = self.getRemovedPos()
				removedPiece.obj.setPos(LPoint3(rX,rY,rZ))
				removedPiece.obj.reparentTo(self.removed)
			self.pieceList[pX][pY][pZ] = movePiece
			movePiece.obj.setPos(LPoint3(pX-6,pY-2,pZ-6))
			movePiece.firstMove = True
			self.currPlayer = 1-self.currPlayer
		else:
			self.printList.append("No redo move!")

	def hint(self):
		# Get hint move from AI
		move = self.AI.move()
		(x,y,z) = move[0]
		self.board.board[x][y][z].square.setColor(HIGHLIGHT3)
		(x,y,z) = move[1]
		self.board.board[x][y][z].square.setColor(HIGHLIGHT3)

	def getRemovedPos(self):
		for (piece,posi) in self.removedBlackList:
			if self.currPiece == piece:
				x = len(self.removedBlackList)-1
				return (x-4,4,-5)
		x = len(self.removedWhiteList)-1
		return (x-4,-2,-5)

	def removePiece(self):
		if self.currLabel not in self.prevPossMove:
			return
		(x,y,z) = self.prevLabel
		self.pieceList[x][y][z] = None
		(x,y,z) = self.currLabel
		self.prevPiece.obj.setPos(LPoint3(x-6,y-2,z-6))
		self.moveList.append((self.prevLabel,self.currLabel))
		self.prevPiece.firstMove = True
		# Check the removed piece's color
		if int(self.currPiece.colorR) == 0:
			self.removedBlackList.append((self.currPiece,self.currLabel))
		else:
			self.removedWhiteList.append((self.currPiece,self.currLabel))
		self.pieceList[x][y][z] = self.prevPiece
		(x,y,z) = self.getRemovedPos()
		# Display the removed piece on the side of the board
		self.currPiece.obj.setPos(LPoint3(x,y,z))
		self.currPiece.obj.reparentTo(self.removed)
		self.currPiece = None
		self.currPlayer = 1-self.currPlayer
		self.undoList = []

	def highlightMove(self):
		for label in self.possibleMove:
			(x,y,z) = label
			self.board.board[x][y][z].square.setColor(HIGHLIGHT)

	def undoHighLight(self):
		for x in range(len(self.board.board)):
			for y in range(len(self.board.board[0])):
				for z in range(len(self.board.board[0][0])):
					if self.board.board[x][y][z] != False:
						color = self.oriBoard[x][y][z].color
						self.board.board[x][y][z].square.setColor(color)

	def makeAIMove(self):
		self.printList.append("White has made a move!")
		# Get where to move to
		(x,y,z) = self.AI.move()[1]
		# Determine move/remove
		if self.pieceList[x][y][z] != None:
			if int(self.pieceList[x][y][z].colorR) != self.currPlayer:
				self.printList.append("Your piece has been removed!")
				self.removedBlackList.append((self.pieceList[x][y][z],(x,y,z)))
				(rX,rY,rZ) = (len(self.removedBlackList)-6,4,-5)
				self.pieceList[x][y][z].obj.setPos(LPoint3(rX,rY,rZ))
				self.pieceList[x][y][z].obj.reparentTo(self.removed)
			else:
				self.printList.append("You cannot move here!")
		# Get where to move from
		(pX,pY,pZ) = self.AI.move()[0]
		# Move the piece
		self.currPiece = self.pieceList[pX][pY][pZ]
		self.pieceList[pX][pY][pZ] = None
		self.currPiece.firstMove = True
		self.pieceList[x][y][z] = self.currPiece
		self.currPiece.obj.setPos(LPoint3(x-6,y-2,z-6))
		self.moveList.append(((pX,pY,pZ),(x,y,z)))
		self.currPlayer = 1-self.currPlayer
		
		self.currPiece = None
		self.prevPiece = None
		self.prevLabel = None
		self.possibleMove = []
		self.prevPossMove = []

	def oneClick(self):
		x = base.mouseWatcherNode.getMouseX()
		y = base.mouseWatcherNode.getMouseY()
		self.mousePosition = LPoint3(x, y, 0)	
		# Check in board move or piece move mode
		if not self.boardMove:
			# Get current clicked square object
			self.currSquare = self.getSquare()
			# Check if current board has piece
			if self.getPiece() != None:
				if int(self.getPiece().colorR) == self.currPlayer:
					self.currPiece = self.getPiece()
					self.possibleMove = rules.labelLegalMove(self)
				else:
					self.currPiece = self.getPiece()
					self.possibleMove = []
			else:
				self.currPiece = None
				self.possibleMove = []	
			# Check if we are making a move
			if self.prevPiece != None:
				if self.currPiece == None:
					self.movePiece()
				elif self.currPiece != None and int(self.currPiece.colorR) != self.currPlayer:
					self.removePiece()

			# Undo selected square
			if self.prevLabel != None:
				(x,y,z) = self.prevLabel
				self.board.board[x][y][z].setColor(self.oriBoard[x][y][z].color)

			self.undoHighLight()
			self.highlightMove()
			# Highlight selected square
			if self.getSquare() != False:
				self.currSquare.setColor(HIGHLIGHT2)

			self.prevPiece = self.currPiece
			self.prevLabel = self.currLabel
			self.prevPossMove = self.possibleMove
		else:
			self.undoHighLight()
			self.currSquare = self.getSquare()
			(x,y,z) = self.currLabel
			# Check whether this move is selecting board or moving board
			if self.prevBoard == None:
				self.count = 0
				if z%2 == 0 or self.getPiece() != None:
					self.printList.append("You cannot move this board!")
				else:
					self.currBoard = self.getBoard()
					for (x,y,z) in self.currBoard:
						# Highlight current board
						self.board.board[x][y][z].setColor(HIGHLIGHT2)
						if self.pieceList[x][y][z] != None:
							if int(self.pieceList[x][y][z].colorR) != self.currPlayer:
								self.count += 1
							self.count += 1

					self.possibleMove = rules.labelLegalBoard(self)
					# Highlight possible moves
					for (x,y,z) in self.possibleMove:
						self.board.board[x][y][z].setColor(HIGHLIGHT)
			else: 
				# Check if the move is legal
				if self.count > 1:
					self.printList.append("You cannot move this board!")
				else:
					self.moveBoard()

			self.prevBoard = self.currBoard
			self.prevLabel = self.currLabel
			self.prevPossMove = self.possibleMove
			self.currBoard = None

	def getBoard(self):
		(x,y,z) = self.currLabel
		squareList = []
		dList = [(1,-1),(1,1),(-1,-1),(-1,1),(1,0),(-1,0),(0,1),(0,-1),(0,0)]
		if z % 2 == 1:
			for (dX,dY) in dList:
				# Check if the square label is in range and has square
				if (x+dX >= 0 and x+dX <= 9 and y+dY >= 0 and y+dY <= 5 and 
					self.board.board[x+dX][y+dY][z] != False):
					squareList.append((x+dX,y+dY,z))
		return sorted(squareList)

	def moveBoard(self):
		if self.currLabel in self.prevPossMove:
			(cX,cY,cZ) = self.currLabel
			(pX,pY,pZ) = self.prevLabel
			# Select the initial square as the bottom left one
			if cY == 1:
				cY -= 1
			if cX%2 == 1:
				cX -= 1
			cZ += 1
			squareList = [(cX,cY,cZ),(cX,cY+1,cZ),(cX+1,cY,cZ),(cX+1,cY+1,cZ)]
			for i in range(len(self.prevBoard)):
				(x,y,z) = self.prevBoard[i]
				(cX,cY,cZ) = squareList[i]
				self.board.board[cX][cY][cZ] = self.board.board[x][y][z]
				self.board.board[cX][cY][cZ].setLabel(cX,cY,cZ)
				self.board.board[x][y][z].square.setPos(LPoint3(cX-6,cY-2,cZ-6))
				self.oriBoard[cX][cY][cZ] = self.oriBoard[x][y][z]
				self.oriBoard[cX][cY][cZ].setLabel(cX,cY,cZ)
				self.oriBoard[x][y][z] = False
				self.board.board[x][y][z] = False
				# If the board has piece, move the piece as well
				if self.pieceList[x][y][z] != None:
					self.pieceList[x][y][z].obj.setPos(LPoint3(cX-6,cY-2,cZ-6))
					self.pieceList[cX][cY][cZ] = self.pieceList[x][y][z]
					self.pieceList[x][y][z] = None
			# Move the corresponding addon cylinder
			for addOnObj in self.addOnList:
				(aX,aY,aZ) = addOnObj.getPosi()
				if self.board.board[int(aX+6)][int(aY+2)][int(aZ+7)] == False:
					(cX,cY,cZ) = squareList[0]
					addOnObj.setPosi(cX-6,cY-2,cZ-7)
		self.count = 0
		self.currBoard = None
		self.prevBoard = None
		self.prevLabel = None
		self.possibleMove = []
		self.prevPossMove = []
		self.undoList = []
		self.moveList = []
		self.currPlayer = 1-self.currPlayer

	def click(self):
		if self.mode == 1:
			if self.currPlayer == 0:
				self.oneClick()
		if self.mode == 2:
			self.oneClick()

	def hasPiece(self,row,col,level):
		if self.pieceList[row][col][level] == None:
			return False
		return True

	def getPiece(self):
		if self.currLabel != None:
			(x,y,z) = self.currLabel
			return self.pieceList[x][y][z]

	def getSquare(self):
		if self.currLabel != None:
			x = self.currLabel[0]
			y = self.currLabel[1]
			z = self.currLabel[2]
			return self.board.board[x][y][z]

	def clickRelease(self):
		self.mousePosition = None

	def endGame(self):
		self.endFrame.show()
		self.playFrame.hide()
		if self.currPlayer == 0:
			currPlayer = "White"
		else:
			currPlayer = "Black"
		try: self.drawWinner.destroy()
		except: pass
		# Display winner
		self.drawWinner = OnscreenText(text="%s wins!" % currPlayer, font=self.font, 
									fg=(1,1,1,1), parent=self.endFrame, 
									scale = .1, pos=(0,0,.2))
		self.mode *= -1
		
	def mouseTask(self,task):
		try:
			self.player.destroy()
			for string in self.printStr:
				string.destroy()
		except:
			pass
		# Check if current status is checkmate
		if rules.checkMate(self):
			if len(self.printList) == 0 or self.printList[-1] != "StaleMate!":
				self.printList.append("StaleMate!")
		# Check if the game has ended
		if self.mode >= 0:
			# Display status bar
			posi = 0.36
			if len(self.printList) > 7:
				self.printList.pop(0)
			for string in self.printList:
				self.printStr.append(OnscreenText(text="%s" % string, style=1, fg=(.2,.2,.2,1), 
												font=self.font, parent=self.playFrame,
											  	pos=(1.55, posi), scale = .045))
				posi -= .05
			self.currKing = None
			for x in range(len(self.board.board)):
				for y in range(len(self.board.board[0])):
					for z in range(len(self.board.board[0][0])):
						if (self.pieceList[x][y][z] != None and
						self.pieceList[x][y][z].model.split("/")[1] == "king" and
						int(self.pieceList[x][y][z].colorR) == self.currPlayer):
							self.currKing = (x,y,z)
			if self.currKing == None:
				self.endGame()
			self.currKing = None
			if self.currPlayer:
				currPlayer = "White"
				if self.mode == 1:
					self.makeAIMove()
			else:
				currPlayer = "Black"
			# Display current player
			self.player = OnscreenText(text="Current Player: %s" % currPlayer,
											 style=1, fg=(1,1,1,1), parent=self.playFrame,
											 pos=(1.47, -.02), scale = .045)

			# Cited from https://www.panda3d.org/manual/index.php/Sample_Programs:_Chessboard
			if self.mouseWatcherNode.hasMouse():
				x = self.mouseWatcherNode.getMouseX()
				y = self.mouseWatcherNode.getMouseY()
				self.pickerRay.setFromLens(self.camNode, x, y)

				self.cTrav.traverse(self.square)
				if self.collHandler.getNumEntries() > 0:
					# if we have hit something, sort the hits so that the closest is first
					self.collHandler.sortEntries()
					pickedObj = self.collHandler.getEntry(0).getIntoNodePath()
					pickedObj = pickedObj.getTag('square')
					x = int(pickedObj.split(",")[0])
					y = int(pickedObj.split(",")[1])
					z = int(pickedObj.split(",")[2])
					# Set current label as a tuple
					self.currLabel = (x,y,z)

		return Task.cont

	# Cited from https://www.panda3d.org/manual/index.php/Sample_Programs:_Chessboard
	def setupLights(self):
		# This function sets up default lighting
		ambientLight = AmbientLight("ambientLight")
		ambientLight.setColor((.8, .8, .8, 1))

		directionalLight = DirectionalLight("directionalLight")
		directionalLight.setDirection(LVector3(0, 45, -45))
		directionalLight.setColor((0.2, 0.2, 0.2, 1))
		render.setLight(render.attachNewNode(directionalLight))

		render.setLight(render.attachNewNode(ambientLight))
		plight = PointLight('plight')
		plight.setColor(VBase4(0.2, 0.2, 0.2, 1))
		plnp = render.attachNewNode(plight)
		plnp.setPos(10, 20, 0)
		render.setLight(plnp)

app = ChessGame()
app.run()

