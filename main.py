import os
from idlelib.tooltip import Hovertip
from _tkinter import TclError
from tkinter import ttk, messagebox, filedialog
import tkinter as tk

import search
from constants import *


class GameGrid(tk.Canvas):
    """
    canvas area where the game grid is displayed
    """
    def __init__(self, parent, canvas_size=500, *args, **kwargs):
        super().__init__(parent, width=canvas_size, height=canvas_size, bg=PATH_COLOR, *args, **kwargs)
        self.grid_size = 0
        self.canvas_size = canvas_size
        self.items = []
        self.start_piece = None
        self.end_piece = None
        self.showing_solution = False

    def create_piece(self, y, x):
        """add a blank piece to the grid with event listeners on each piece
         so that it can be clicked or dragged to change the piece type"""
        piece_size = self.canvas_size / self.grid_size
        rect = self.create_rectangle(((x * piece_size), (y * piece_size)),
                                     (x * piece_size + piece_size, y * piece_size + piece_size), fill=PATH_COLOR)
        self.tag_bind(rect, "<B1-Motion>", self.change_to_wall)
        self.tag_bind(rect, "<Button-1>", self.change_to_wall)
        self.tag_bind(rect, "<B3-Motion>", self.remove_wall)
        self.tag_bind(rect, "<Button-3>", self.remove_wall)

    def change_to_wall(self, event):
        """convert the piece type to a wall"""
        if self.showing_solution:
            self.reset_grid()

        x, y = self.find_piece_position(event.x, event.y)
        self.place_piece(x, y, kind=MAZE_TILE.WALL)

    def remove_wall(self, event):
        """convert the piece type to a path piece"""
        if self.showing_solution:
            self.reset_grid()
        x, y = self.find_piece_position(event.x, event.y)
        self.place_piece(x, y, kind=MAZE_TILE.PATH)

    def place_piece(self, x, y, kind):
        """place any kind of piece on the grid"""
        if self.items[y][x] == kind.START or self.items[y][x] == kind.END:
            return

        match kind:
            case kind.PATH:
                color = PATH_COLOR
            case kind.WALL:
                color = WALL_COLOR
            case kind.START:
                color = START_COLOR
                if self.start_piece:
                    self.place_piece(self.start_piece[0], self.start_piece[1], kind.WALL)
                self.start_piece = (x, y)
            case kind.END:
                color = END_COLOR
                if self.end_piece:
                    self.place_piece(self.end_piece[0], self.end_piece[1], kind.WALL)
                self.end_piece = (x, y)
            case _:
                raise Exception("Piece color is not set")
        self.itemconfig(self.get_piece(x, y), fill=color)
        self.items[y][x] = kind

    def find_piece_position(self, x, y):
        """given the mouse coordinates of a piece find the x and y index locations for that piece"""
        piece_size = self.canvas_size / self.grid_size
        cordx, cordy = int(x / piece_size), int(y / piece_size)

        if cordx < 0:
            cordx = 0

        if cordy < 0:
            cordy = 0

        if cordy > self.grid_size - 1:
            cordy = self.grid_size - 1

        if cordx > self.grid_size - 1:
            cordx = self.grid_size - 1

        return cordx, cordy

    def get_piece(self, cordx, cordy):
        """given the index locations of a piece return the rectangle object of the piece"""
        piece_size = self.canvas_size / self.grid_size
        return self.find_closest(cordx * piece_size + piece_size / 2, cordy * piece_size + piece_size / 2)

    def set_grid_size(self, size):
        """set the size of the grid, add a start and end point"""
        self.clear_grid()
        self.grid_size = size
        self.items = [[MAZE_TILE.PATH for _ in range(size)] for _ in range(size)]
        for x in range(size):
            for y in range(size):
                self.create_piece(x, y)
                self.place_piece(x, y, MAZE_TILE.PATH)
        if size >= 2:
            self.place_piece(0, 0, MAZE_TILE.START)
            self.place_piece(size - 1, size - 1, MAZE_TILE.END)

    def clear_grid(self):
        """remove all pieces from the grid"""
        self.delete("all")
        self.items = []
        self.start_piece = None
        self.end_piece = None

    def show_solution(self, x_y_list, explored=None):
        """color the pieces in the path that are the solution the correct color. If explored is passed in show the
        explored pieces in a different color"""
        if explored is None:
            explored = set()

        for y, x in explored:
            self.itemconfig(self.get_piece(x, y), fill=EXPLORED_COLOR)

        for y, x in x_y_list:
            self.itemconfig(self.get_piece(x, y), fill=SOLUTION_COLOR)

        self.itemconfig(self.get_piece(*self.start_piece), fill=START_COLOR)
        self.itemconfig(self.get_piece(*self.end_piece), fill=END_COLOR)
        self.showing_solution = True

    def reset_grid(self):
        """re put all the walls on the grid in the correct position without the explored and solution tiles showing"""
        self.showing_solution = False
        items = self.items
        self.set_grid_size(len(items))
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                self.place_piece(x, y, items[y][x])


class Application(ttk.Frame):
    def __init__(self, title, master=None):
        """create the main application window"""
        ttk.Frame.__init__(self, master)
        self.pack(anchor=tk.CENTER, expand=True)
        self.master.title(title)
        self.master.geometry("680x550")
        self.solution = None
        self.explored = None
        self.current_search = None

        self.options_bar = ttk.Frame(self)
        self.options_bar.pack()

        self.grid_size = tk.IntVar()
        self.gridSizeEntry = NumberEntryBox(self.options_bar, textvariable=self.grid_size)
        self.gridSizeEntry.grid(column=0,row=0)

        self.bfs = ttk.Button(self.options_bar, text="BFS", command=self.breadth_first_search)
        Hovertip(self.bfs, 'Breadth first search')
        self.bfs.grid(column=1,row=0)

        self.dfs = ttk.Button(self.options_bar, text="DFS", command=self.depth_first_search)
        Hovertip(self.dfs, 'Depth first search')
        self.dfs.grid(column=2,row=0)

        self.toggle_solution = ttk.Button(self.options_bar, text="Hide Solution", command=self.toggle_solution)
        self.toggle_solution.grid(column=3,row=0)

        self.show_explored_var = tk.BooleanVar()
        self.show_explored_var.trace_add("write", self.show_explored)
        self.show_explored_var.set(True)
        self.show_explored = ttk.Checkbutton(self.options_bar, text="Show Explored", variable=self.show_explored_var)
        self.show_explored.grid(column=4,row=0)

        self.save_image_button = ttk.Button(self.options_bar, text="Save Image", command=self.save_image)
        self.save_image_button.grid(column=5,row=0)

        self.explored_states_label = ttk.Label(self.options_bar, text="Explored States: 0")
        self.explored_states_label.grid(column=6,row=0)

        self.gameGrid = GameGrid(self)
        self.gameGrid.pack(anchor=tk.CENTER, expand=True)

        self.grid_size.trace_add("write", self.createGameGrid)
        self.grid_size.set(20)

    def createGameGrid(self, *args):
        """when grid size changes re draw the games grid"""
        try:
            size = self.grid_size.get()
        except TclError:
            size = 0
        self.gameGrid.set_grid_size(size)

    def breadth_first_search(self):
        """run a breadth first search"""
        self.hide_solution()
        try:
            m = search.Maze(self.gameGrid.items)
            self.current_search = SEARCH_TYPE.BREADTH_FIRST
            m.solve(SEARCH_TYPE.BREADTH_FIRST)
            self.explored_states_label.config(text=f"Explored States: {m.num_explored}")

            # 1== x,y pairs and 0 == directions
            self.solution = m.solution[1]
            self.explored = m.explored
            self.show_solution()
        except Exception as e:
            messagebox.showerror('Error', e)

    def depth_first_search(self):
        """run a depth first search"""
        self.hide_solution()

        try:
            m = search.Maze(self.gameGrid.items)
            self.current_search = SEARCH_TYPE.DEPTH_FIRST
            m.solve(SEARCH_TYPE.DEPTH_FIRST)
            self.explored_states_label.config(text=f"Explored States: {m.num_explored}")
            # 1== x,y pairs and 0 == directions
            self.solution = m.solution[1]
            self.explored = m.explored
            self.show_solution()
        except Exception as e:
            messagebox.showerror('Error', e)

    def save_image(self):
        """ask user where to save the image to"""
        try:
            file = filedialog.asksaveasfile(defaultextension=".png")
            if file:
                m = search.Maze(self.gameGrid.items)
                if self.current_search != None:
                    m.solve(self.current_search)
                show_solution = self.toggle_solution['text'] == "Hide Solution"
                m.output_image(file.name, show_solution=show_solution, show_explored=self.show_explored_var.get())
                os.startfile(file.name)
        except Exception as e:
            messagebox.showerror('Error', e)
            raise e

    def show_explored(self, *args, **kwargs):
        """runs when the show explore checkbox is toggled"""

        # solution is currently being shown so rerender it
        if self.toggle_solution['text'] == "Hide Solution":
            self.hide_solution()
            self.show_solution()

    def hide_solution(self, *args, **kwargs):
        """reset the game grid and keep the walls, start, and end pieces"""

        if self.solution and self.explored:
            self.gameGrid.reset_grid()
        self.toggle_solution['text'] = "Show Solution"

    def show_solution(self):
        """show the path from the start to the end"""

        if self.solution and self.explored:
            if self.show_explored_var.get():
                self.gameGrid.show_solution(self.solution, explored=self.explored)
            else:
                self.gameGrid.show_solution(self.solution, explored=[])
        self.toggle_solution['text'] = "Hide Solution"

    def toggle_solution(self):
        """toggle between the start and end of the solution"""

        if self.toggle_solution['text'] == "Hide Solution":
            self.hide_solution()
        else:
            self.show_solution()


class NumberEntryBox(ttk.Entry):
    """create a input box that only allows a number between 0 and 100"""

    def __init__(self, *args, **kwargs):
        super().__init__(validate='key', *args, **kwargs)
        self['validatecommand'] = (self.register(self.isNumber), '%P', '%d')

    def isNumber(self, inStr, acttyp):
        # if inserting
        if acttyp == '1':
            if not inStr.isdigit():
                return False
            if int(inStr) > 100 or int(inStr) < 0:
                return False
        return True


if __name__ == '__main__':
    app = Application('Search Algorithms')
    app.mainloop()

