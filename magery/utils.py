import io


class IndentedIO(io.IOBase):
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def writelines(self, lines):
        self.wrapped.writelines(["    " + line for line in lines])
