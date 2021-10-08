from blessed import Terminal


def editor(terminal: Terminal, width, default=''):

    with terminal.location():
        print(terminal.on_blue(' '*width))

    string = default

    with terminal.location():
        print(terminal.red_on_blue + string, end='')

        with terminal.cbreak():
            while True:
                val = terminal.inkey()
                if val.code == terminal.KEY_ENTER:
                    break
                elif val == '\x1b' or val.code == terminal.KEY_ESCAPE:
                    string = None
                    break
                elif val.code == terminal.KEY_BACKSPACE:
                    if string:
                        string = string[:-1]
                        print('\b \b', end='')
                elif val.isascii():
                    if len(string) < width:
                        string += val
                        print(val, end='')

    with terminal.location():
        print(terminal.ljust(string if string else '', width=width, fillchar=' '))

    return string


if __name__ == '__main__':
    term = Terminal()

    print(term.green('Prompt:'), end='')
    result = editor(term, 20, 'TEST')

    print('\nReturn value:' + result)
