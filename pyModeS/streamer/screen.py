from __future__ import print_function, division
import os
import curses
import numpy as np
import time
from threading import Thread

COLUMNS = [
    ('lat', 10),
    ('lon', 10),
    ('alt', 7),
    ('gs', 5),
    ('tas', 5),
    ('ias', 5),
    ('mach', 7),
    ('roc', 7),
    ('trk', 10),
    ('hdg', 10),
    ('ver', 4),
    ('NIC', 5),
    ('NACv', 5),
    ('NACp', 5),
    ('SIL', 5),
    ('live', 6),
]

class Screen(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.screen = curses.initscr()
        curses.noecho()
        curses.mousemask(1)
        self.screen.keypad(True)
        self.y = 3
        self.x = 1
        self.offset = 0
        self.acs = {}
        self.lock_icao = None


    def reset_cursor_pos(self):
        self.screen.move(self.y, self.x)

    def update_data(self, acs):
        self.acs = acs

    def draw_frame(self):
        self.screen.border(0)
        self.screen.addstr(0, 2, "Online aircraft ('ESC' to exit, 'Enter' to lock one)")

    def update(self):
        if len(self.acs) == 0:
            return

        resized = curses.is_term_resized(self.scr_h, self.scr_w)
        if resized is True:
            self.scr_h, self.scr_w = self.screen.getmaxyx()
            self.screen.clear()
            curses.resizeterm(self.scr_h, self.scr_w)

        self.screen.refresh()
        self.draw_frame()

        row = 1

        header = '  icao'
        for c, cw in COLUMNS:
            header += (cw-len(c))*' ' + c

        # fill end with spaces
        header += (self.scr_w - 2 - len(header)) * ' '

        if len(header) > self.scr_w - 2:
            header = header[:self.scr_w-3] + '>'


        self.screen.addstr(row, 1, header)

        row +=1
        self.screen.addstr(row, 1, '-'*(self.scr_w-2))

        icaos = np.array(list(self.acs.keys()))
        icaos = np.sort(icaos)

        for row in range(3, self.scr_h - 3):
            idx = row + self.offset

            if idx > len(icaos) - 1:
                line = ' '*(self.scr_w-2)

            else:
                line = ''

                icao = icaos[idx]
                ac = self.acs[icao]

                line += icao

                for c, cw in COLUMNS:
                    if c=='live':
                        val = int(time.time() - ac[c])
                    elif ac[c] is None:
                        val = ''
                    else:
                        val = ac[c]
                    val_str = str(val)
                    line += (cw-len(val_str))*' ' + val_str

                # fill end with spaces
                line += (self.scr_w - 2 - len(line)) * ' '

                if len(line) > self.scr_w - 2:
                    line = line[:self.scr_w-3] + '>'

            if (icao is not None) and (self.lock_icao == icao):
                self.screen.addstr(row, 1, line, curses.A_STANDOUT)
            elif row == self.y:
                self.screen.addstr(row, 1, line, curses.A_BOLD)
            else:
                self.screen.addstr(row, 1, line)

        self.screen.addstr(self.scr_h-3, 1, '-'*(self.scr_w-2))

        total_page = len(icaos) // (self.scr_h - 4) + 1
        current_page = self.offset // (self.scr_h - 4) + 1
        self.screen.addstr(self.scr_h-2, 1, '(%d / %d)' % (current_page, total_page))

        self.reset_cursor_pos()

    def run(self):
        self.draw_frame()
        self.scr_h, self.scr_w = self.screen.getmaxyx()

        while True:
            c = self.screen.getch()

            if c == 27:
                curses.endwin()
                os._exit(1)
            elif c == curses.KEY_HOME:
                self.x = 1
                self.y = 1
            elif c == curses.KEY_NPAGE:
                offset_intent = self.offset + (self.scr_h - 4)
                if offset_intent < len(self.acs) - 5:
                    self.offset = offset_intent
            elif c == curses.KEY_PPAGE:
                offset_intent = self.offset - (self.scr_h - 4)
                if offset_intent > 0:
                    self.offset = offset_intent
                else:
                    self.offset = 0
            elif c == curses.KEY_DOWN :
                y_intent = self.y + 1
                if y_intent < self.scr_h - 3:
                    self.y = y_intent
            elif c == curses.KEY_UP:
                y_intent = self.y - 1
                if y_intent > 2:
                    self.y = y_intent
            elif c == curses.KEY_ENTER or c == 10 or c == 13:
                self.lock_icao = (self.screen.instr(self.y, 1, 6)).decode()
            elif c == curses.KEY_F5:
                self.screen.refresh()
                self.draw_frame()
