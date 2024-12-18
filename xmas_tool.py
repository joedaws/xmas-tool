from __future__ import annotations
import curses
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import random
import time
import uuid


def time_until_christmas(timezone_offset: int):
    now_utc = datetime.now(timezone.utc)

    # Apply the timezone offset
    offset = timedelta(hours=timezone_offset)
    now_local = now_utc + offset

    # Determine the year for the next Christmas
    current_year = now_local.year
    christmas_this_year = datetime(current_year, 12, 25, 0, 0, 0, tzinfo=timezone(offset))

    # Check if Christmas has already passed this year
    if now_local >= christmas_this_year:
        next_christmas = datetime(current_year + 1, 12, 25, 0, 0, 0, tzinfo=timezone(offset))
    else:
        next_christmas = christmas_this_year

    # Calculate the time difference
    delta = next_christmas - now_local

    # Extract days, hours, minutes, and seconds
    days = delta.days
    seconds_in_day = delta.seconds
    hours = seconds_in_day // 3600
    minutes = (seconds_in_day % 3600) // 60
    seconds = (seconds_in_day % 3600) % 60

    return {
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
    }


class Canvas:
    def __init__(self, nrows, ncols):
        self.nrows = nrows
        self.ncols = ncols
        self.elements = {}

    def upsert(self, canvas_element: CanvasElement):
        self.elements[canvas_element.id] = canvas_element

    def remove(self, canvas_element: CanvasElement):
        if element.name in self.elements:
            removed_element = self.elements.pop(element.name)
        else:
            print(f"No element found with name '{element.name}'.")

    def get_element(self, name: str):
        return self.elements.get(name, None)

    def render(self):
        """Renders the canvas as a string and prints it."""

        canvas = [[' ' for _ in range(self.ncols)] 
                       for _ in range(self.nrows)]
        element_list = sorted(
                [e for k, e in self.elements.items()],
                key= lambda elem: elem.z
                )
        for element in element_list:
            for cell in element.cell_list:
                if not Cell.in_bounds(cell, self.nrows, self.ncols):
                    continue
                canvas[cell.x][cell.y] = cell.c

        return canvas


@dataclass
class Cell:
    x: int
    y: int
    c: str

    @staticmethod
    def in_bounds(cell: Cell, nrows: int, ncols: int) -> Bool:
        if cell.x >= 0 and cell.x < nrows and cell.y >= 0 and cell.y < ncols:
            return True
        return False


class CanvasElement:
    def __init__(self, z: int, cell_list: [Cell]):
        self.id = str(uuid.uuid4())
        self.z = z
        self.cell_list = cell_list

    @staticmethod
    def merge(element1: CanvasElement, element2: CanvasElement) -> CanvasElement:
        return CanvasElement(
                z=element1.z, 
                cell_list = element1.cell_list + element2.cell_list
                )


class Message:
    def __init__(
            self, 
            start_row: int,  
            start_col: int,
            message: str):
        self.start_row = start_row 
        self.start_col = start_col 
        self.message = message
        self.message_length = len(message)
        self.cell_list = self._build()

    def _build(self):
        cell_list = [
            Cell(x=self.start_row, y=y, c=self.message[i]) 
            for i, y in enumerate(
                range(self.start_col, self.start_col + self.message_length
                    )
            )]
        return cell_list


class Box:
    TOP_LEFT_CORNER = '╭'
    TOP_RIGHT_CORNER = '╮'
    BOTTOM_LEFT_CORNER = '╰'
    BOTTOM_RIGHT_CORNER = '╯'
    HORIZONTAL_EDGE = '─'
    VERTICAL_EDGE = '│'

    def __init__(
            self, 
            start_row: int,
            end_row: int,
            start_col: int,
            end_col: int,
            filled: bool):
        self.start_row = start_row
        self.end_row = end_row
        self.start_col = start_col
        self.end_col = end_col
        self.filled = filled
        self.cell_list = self._build()

    def _build(self):
        cell_list = []

        if self.filled:
            for i in range(self.start_row + 1, self.end_row):
                for j in range(self.start_col + 1, self.end_col):
                    cell_list.append(
                        Cell(x=i, y=j, c=' ')
                    )

        # Top edge
        cell_list.append(
            Cell(
                x=self.start_row, 
                y=self.start_col, 
                c=self.TOP_LEFT_CORNER
            )
        )
        cell_list.append(
            Cell(
                x=self.start_row, 
                y=self.end_col, 
                c=self.TOP_RIGHT_CORNER
            )
        )
        for i in range(self.start_col+1, self.end_col):
            cell_list.append(
                Cell(x=self.start_row, y=i, c=self.HORIZONTAL_EDGE)
            )

        # Bottom edge
        cell_list.append(
            Cell(
                x=self.end_row, 
                y=self.start_col, 
                c=self.BOTTOM_LEFT_CORNER
            )
        )
        cell_list.append(
            Cell(
                x=self.end_row, 
                y=self.end_col, 
                c=self.BOTTOM_RIGHT_CORNER
            )
        )
        for i in range(self.start_col+1, self.end_col):
            cell_list.append(
                Cell(x=self.end_row, y=i, c=self.HORIZONTAL_EDGE)
            )

        # Left and right edges
        for i in range(self.start_row + 1, self.end_row):
            cell_list.append(
                Cell(x=i, y=self.start_col, c=self.VERTICAL_EDGE)
            )
            cell_list.append(
                Cell(x=i, y=self.end_col, c=self.VERTICAL_EDGE)
            )

        return cell_list


class XmasTree:
    def __init__(self, start_row: int, start_col: int, height: int):
        self.start_row = start_row
        self.start_col = start_col
        self.height = height
        self.width = 2 * height - 1
        self.cell_list = self._build()
        self._add_ornaments(9)

    def _build(self):
        cell_list = []

        cell_list.append(
            Cell(x=self.start_row, y=self.start_col + self.width // 2, c='✪')
        )

        # Build tree leaves
        for i in range(1,self.height):
            mid = self.width // 2
            for j in range(mid - i, mid + i + 1):
                cell_list.append(
                    Cell(x=self.start_row + i, y=self.start_col + j, c ='*')
                )

        # Build tree trunk
        trunk_width = self.height // 3
        trunk_width = trunk_width if trunk_width % 2 == 1 else trunk_width + 1
        trunk_height = self.height // 4
        trunk_start = self.width // 2 - trunk_width // 2
        for i in range(self.height, self.height + trunk_height):
            for j in range(trunk_start, trunk_start + trunk_width):
                cell_list.append(
                    Cell(x=self.start_row + i, y=self.start_col + j, c ='*')
                )

        return cell_list

    def _add_ornaments(self, n: int):
        """Randomly add 'O' ornaments to the tree leaves.
        :param n: Number of ornaments to add
        """
        num_cell = len(self.cell_list)
        for _ in range(n):
            while True:
                i = random.randint(1, num_cell-1)
                if self.cell_list[i].c == '*':
                    self.cell_list[i].c = 'O'
                    break


class CanvasElementFactory:
    @staticmethod
    def create_box(
            start_row: int,
            end_row: int,
            start_col: int,
            end_col: int,
            filled: bool,
            z: int):
        box = Box(
                start_row=start_row,
                end_row=end_row,
                start_col=start_col,
                end_col=end_col,
                filled=filled)
        return CanvasElement(z=z, cell_list=box.cell_list)

    @staticmethod
    def create_message(
            start_row: int, 
            start_col: int, 
            message: str, 
            z: int):
        message = Message(
                start_row = start_row,
                start_col = start_col,
                message=message)
        return CanvasElement(z=z, cell_list=message.cell_list)

    @staticmethod
    def create_xmas_tree(
            start_row: int, 
            start_col: int, 
            height: int,
            z: int):
        tree = XmasTree(
                height=height,
                start_row=start_row,
                start_col=start_col)
        return CanvasElement(z=z, cell_list=tree.cell_list)


def xmas(mouth_open=False):
    nrows = 20
    ncols = 70
    canvas = Canvas(nrows, ncols)
    factory = CanvasElementFactory
    message = factory.create_message(
            start_row = 0,
            start_col = 5,
            message='🅧🅜🅐🅢', 
            z=10)
    border = factory.create_box(
            start_row = 0,
            end_row = nrows - 1,
            start_col = 0,
            end_col = ncols - 1,
            filled = False,
            z=5)
    tree = factory.create_xmas_tree(
            height = 15,
            start_row = 2,
            start_col = 2,
            z=1)
    # build face out of box and message
    face = factory.create_box(
            start_row = 7,
            end_row = 11,
            start_col = 9,
            end_col = 23,
            filled = True,
            z=4)
    if not mouth_open:
        eyes = factory.create_message(
                start_row = 9,
                start_col = 15,
                message='｡◕◡◕｡', 
                z=4)
    else:
        eyes = factory.create_message(
                start_row = 9,
                start_col = 15,
                message='｡◕▿◕｡', 
                z=4)

    face = CanvasElement.merge(face, eyes)

    instructions = factory.create_message(
            start_row = nrows - 2,
            start_col = 43,
            message='q - quit', 
            z=10)

    # EST is -5
    until_xmas = time_until_christmas(-5)
    count_down = factory.create_message(
            start_row = 10,
            start_col = 30,
            message=f"{until_xmas['days']} days, {until_xmas['hours']} hours, "\
               f"{until_xmas['minutes']} minutes, {until_xmas['seconds']} seconds",
            z = 10
            )
 
    canvas.upsert(border)
    canvas.upsert(message)
    canvas.upsert(tree)
    canvas.upsert(face)
    canvas.upsert(instructions)
    canvas.upsert(count_down)
    state = canvas.render()

    return state


def animated_loop(stdscr):
    curses.curs_set(0)          # Hide the cursor
    stdscr.nodelay(True)        # Non-blocking input
    fps = 5
    frame = 0

    while True:
        canvas = xmas(
                    (frame % 2 == 0) or (frame % 3 == 0) or (frame % 5 == 0)
                )
    
        # Now draw them on the curses screen
        for i, row in enumerate(canvas):
            stdscr.addstr(i, 0, ''.join(row))

        stdscr.refresh()
        time.sleep(1.0/fps)
        frame += 1 % 100

        key = stdscr.getch()
        if key == ord('q'):
            break

# Example usage:
if __name__ == "__main__":
    curses.wrapper(animated_loop)
