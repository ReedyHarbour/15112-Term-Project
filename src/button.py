from direct.showbase.ShowBase import ShowBase
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
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
import board,piece,rules,chessAI
import sys
import copy

# Initialize buttons on init screen
class InitButton(object):
	def __init__(self, board):
		board.initFrame = DirectFrame(frameColor=(1,1,1,0),
                      frameSize=(-3,3,-2,2), pos=(0, -1, 0))
		board.backGround = OnscreenImage(image='image/background.png', pos=(0,0,0), scale=(2,1,1), parent=board.initFrame)
		board.onePlayerButton = DirectButton(pos=(0,0,-.28), text="One Player", parent=board.initFrame,
                    			   text_fg=(1,1,1,1), command=board.onePlayerGame, scale=.1,
                                   pad=(.2,.1), frameColor=(0.5,0.3,0.2,0), text_font=board.font,
                                   relief=DGG.FLAT)
		board.twoPlayerButton = DirectButton(pos=(0,0,-.47), text="Two Player", text_font=board.font,
                    			   text_fg=(1,1,1,1), command=board.twoPlayerGame, parent=board.initFrame,
                                   scale=.1, pad=(.4,.1), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT)
		board.helpButton = DirectButton(pos=(-.25,0,-.66), text="Help", text_font=board.font,
                    			   text_fg=(1,1,1,1), command=board.tutorial, parent=board.initFrame,
                                   scale=.1, pad=(.4,.1), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT)
		board.exitButton = DirectButton(pos=(.25,0,-.67), text=("Exit"), text_font=board.font,
                    			   text_fg=(1,1,1,1), command=board.exit, parent=board.initFrame,
                                   scale=.1, pad=(.45,.1), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT)

# Initialize buttons on play screen
class PlayButton(object):
	def __init__(self, board):
		background = OnscreenImage(image='image/bar.png', pos=(1.6,0,0), scale = (.5,1,1), parent=board.playFrame)
		background.setTransparency(TransparencyAttrib.MBinary)
		board.boardButton = DirectButton(pos=(1.33, 0, 0.83), text="Board", 
                    			   text_fg=(0.2,0.2,0.2,1), command=board.setBoard,
                                   scale=.05, pad=(.4, .6), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT, text_font=board.font, parent=board.playFrame)
		board.set1 = OnscreenText(text="Status", fg=(1,1,1,1), parent=board.playFrame, 
								scale = .045, pos=(1.32, .435))
		board.undo = DirectButton(pos=(1.55, 0, -.16), text="Undo", 
                    			   text_fg=(0.2,0.2,0.2,1), command=board.undoMove,
                                   scale=.05, pad=(.4, .2), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT, text_font=board.font, parent=board.playFrame,
                                   rolloverSound=None, clickSound=None)
		board.redo = DirectButton(pos=(1.55, 0, -.31), text="Redo", 
                    			   text_fg=(0.2,.2,.2,1), command=board.redoMove,
                                   scale=.05, pad=(.4, .2), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT, text_font=board.font, parent=board.playFrame, 
                                   rolloverSound=None, clickSound=None)
		board.hintButton = DirectButton(pos=(1.55, 0, -.47), text="Hint", 
                    			   text_fg=(.2,.2,.2,1), command=board.hint,
                                   scale=.05, pad=(.4, .2), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT, text_font=board.font, parent=board.playFrame, 
                                   rolloverSound=None, clickSound=None)
		board.changeView = DirectButton(pos=(1.55, 0, -.63), text="Rotate", 
                    			   text_fg=(.2,.2,.2,1), command=board.changeCameraView,
                                   scale=.05, pad=(.4, .2), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT, text_font=board.font, parent=board.playFrame, 
                                   rolloverSound=None, clickSound=None)
		board.resetButton = DirectButton(pos=(1.775, 0, 0.83), text="Reset", 
                    			   text_fg=(0.2,0.2,0.2,1), command=board.resetView,
                                   scale=.05, pad=(.4, .6), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT, text_font=board.font, parent=board.playFrame)
		board.surrender = DirectButton(pos=(1.55, 0, 0.83), text="Surrender", 
                    			   text_fg=(0.2,0.2,0.2,1), command=board.endGame,
                                   scale=.05, pad=(.4, .6), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT, text_font=board.font, parent=board.playFrame)
		board.backButton = DirectButton(pos=(1.73, 0, -.86), text="Back", 
                    			   text_fg=(.2,.2,.2,1), command=board.restartScreen,
                                   scale=.04, pad=(.4, .2), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT, text_font=board.font, parent=board.playFrame, 
                                   rolloverSound=None, clickSound=None)
		board.playHelpButton = DirectButton(pos=(1.38, 0, -.86), text="Help", 
                    			   text_fg=(.2,.2,.2,1), command=board.tutorial,
                                   scale=.04, pad=(.4, .2), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT, text_font=board.font, parent=board.playFrame, 
                                   rolloverSound=None, clickSound=None)
		board.homeButton = DirectButton(pos=(1.55, 0, -.86), text="Home", 
                    			   text_fg=(.2,.2,.2,1), command=board.restartScreen,
                                   scale=.04, pad=(.4, .2), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT, text_font=board.font, parent=board.playFrame, 
                                   rolloverSound=None, clickSound=None)
		board.arrowUp = DirectButton(pos=(1.55, 0, 0.73), text=" ", 
                    			   text_fg=(0.2,0.2,0.2,1), command=board.setKeyUp,
                                   scale=.05, pad=(1.2, .6), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT, text_font=board.font, parent=board.playFrame)
		board.arrowDown = DirectButton(pos=(1.55, 0, 0.6), text=" ", 
                    			   text_fg=(0.2,0.2,0.2,1), command=board.setKeyDown,
                                   scale=.05, pad=(1.2, 1.2), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT, text_font=board.font, parent=board.playFrame)
		board.arrowLeft = DirectButton(pos=(1.33, 0, 0.6), text=" ", 
                    			   text_fg=(0.2,0.2,0.2,1), command=board.setKeyLeft,
                                   scale=.05, pad=(1.2, 1.2), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT, text_font=board.font, parent=board.playFrame)
		board.arrowRight = DirectButton(pos=(1.77, 0, 0.6), text=" ", 
                    			   text_fg=(0.2,0.2,0.2,1), command=board.setKeyRight,
                                   scale=.05, pad=(1.2, 1.2), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT, text_font=board.font, parent=board.playFrame)

# Initialize buttons on tutorial screen
class TutorialButton(object):
	def __init__(self, board):
		board.nextButton = DirectButton(pos=(-1.03, 0, -.72), text="OK", 
                    			   text_fg=(0.2,0.2,0.2,1), command=board.moveToNextTutorial,
                                   scale=.05, pad=(1.2, 1.2), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT, text_font=board.font, parent=board.tutorialFrame)
		board.backButton = DirectButton(pos=(-1.53, 0, -.72), text="Back", 
                    			   text_fg=(0.2,0.2,0.2,1), command=board.resumeScreen,
                                   scale=.05, pad=(1.2, 1.2), frameColor=(0.5,0.3,0.2,0),
                                   relief=DGG.FLAT, text_font=board.font, parent=board.tutorialFrame)