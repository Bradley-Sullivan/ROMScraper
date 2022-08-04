import curses


def main():

    """
    The curses.wrapper function is an optional function that
    encapsulates a number of lower-level setup and teardown
    functions, and takes a single function to run when
    the initializations have taken place.
    """

    curses.wrapper(curses_main)


def curses_main(w):

    """
    This function is called curses_main to emphasise that it is
    the logical if not actual main function, called by curses.wrapper.
    Its purpose is to call several other functions to demonstrate
    some of the functionality of curses.
    """

    w.addstr("-----------------\n")
    w.addstr("| codedrome.com |\n")
    w.addstr("| curses demo   |\n")
    w.addstr("-----------------\n")
    w.refresh()

    # printing(w)

    # moving_and_sleeping(w)

    colouring(w)

    w.addstr("\npress any key to exit...")
    w.refresh()
    w.getch()


def printing(w):

    """
    A few simple demonstrations of printing.
    """

    w.addstr("This was printed using addstr\n\n")
    w.refresh()

    w.addstr("The following letter was printed using addch:- ")
    w.addch('a')
    w.refresh()

    w.addstr("\n\nThese numbers were printed using addstr:-\n{}\n{:.6f}\n".format(123, 456.789))
    w.refresh()


def moving_and_sleeping(w):

    """
    Demonstrates moving the cursor to a specified position before printing,
    and sleeping for a specified period of time.
    These are useful for very basic animations.
    """

    row = 5
    col = 0

    curses.curs_set(False)

    for c in range(65, 91):

        w.addstr(row, col, chr(c))
        w.refresh()
        row += 1
        col += 1
        curses.napms(100)

    curses.curs_set(True)

    w.addch('\n')


def colouring(w):

    """
    Demonstration of setting background and foreground colours.
    """

    if curses.has_colors():

        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_RED)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_GREEN)
        curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_CYAN)

        w.addstr("Yellow on red\n\n", curses.color_pair(1))
        w.refresh()

        w.addstr("Green on green + bold\n\n", curses.color_pair(2) | curses.A_BOLD)
        w.refresh()

        w.addstr("Magenta on cyan\n", curses.color_pair(3))
        w.refresh()

    else:

        w.addstr("has_colors() = False\n");
        w.refresh()


main()