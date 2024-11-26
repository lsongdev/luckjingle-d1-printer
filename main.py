from printer import Printer

if __name__ == "__main__":
    printer = Printer("/dev/rfcomm1")
    printer.print_image_file("cat.jpg")
    printer.print_text("hello world\n\n\n", font="zpix.ttf")