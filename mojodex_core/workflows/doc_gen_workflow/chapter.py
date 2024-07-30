class Chapter:
    def __init__(self, title : str, start : int, end : int):
        self.title = title
        self.start = start
        self.end = end
        self.content = None
    
    @classmethod
    def from_input_string(cls, input_string : str):
        # example string: 0 --> 1871: Introduction et objectifs de la session
        parts = input_string.split(":")
        title = " ".join(parts[1:]).strip()
        
        start, end = parts[0].split(" --> ")

        return cls(title, int(start), int(end))
