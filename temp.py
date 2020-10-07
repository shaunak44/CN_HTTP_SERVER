import mimetypes
t = mimetypes.MimeTypes().guess_type('index.html')[0]
print(type(t), type("asda"))

