#!/usr/bin/env python
# coding=utf-8
"""
streaming upload plugin for tornado. 
can upload the file from "multipart/form-data", 
save it into file system or mongodb, and set the metadata into request arguments.
"""
import tempfile

class UploadHandlerMixin(object):
    boundary = None
    ctx = {}
    def get_boundary(self):
        content_type = self.request.headers.get('Content-Type', '')
        if content_type.startswith("multipart/form-data"):
            fields = content_type.split(";")
            for field in fields:
                k, sep, v = field.strip().partition("=")
                if k == "boundary" and v:
                    if v.startswith(b'"') and v.endswith(b'"'):
                        v = v[1:-1]
                    return v 
        return None

    def get_name_from_header(self, header):
        stuff, p, name = header.partition("=")
        name, p, filename = name.partition("=")
        name, filename, content_type = name.strip("\""), filename.strip("\""), None
        self.ctx = {'name': name}
        if filename:
            name, p, stuff = name.partition("\"")
            filename, p,stuff = filename.partition("\"")
            stuff, p, content_type = stuff.partition(":")
            content_type = content_type.strip()
            self.ctx = {'name': name, 'filename': filename, 'content_type': content_type, 'size': 0}
        return name, filename, content_type

    def add_argument(self, name, value):
        """
        If upload file in request, will save dict to arguments.
        Can not using self.get_argument() to access this params!!!
        """
        if self.request.arguments.get(name, None):
            self.request.arguments[name].append(value)
        else:
            self.request.arguments[name] = [value]

    def _data_received_part(self, part):

        if not self.ctx.get('filename', None):
            self.ctx['value'] = part
        else:
            self.ctx['size'] = self.ctx.get('size', 0) + len(part)
        self.data_received_part(part)

    def _data_received_part_end(self):

        if not self.ctx.get('filename', None):
            self.add_argument(self.ctx.get('name'), self.ctx.get('value'))
        else:
            self.add_argument(self.ctx.get('name'), self.ctx)
        self.data_received_part_end()

    def data_received(self, data):
        if not self.boundary:
            self.boundary = self.get_boundary()

        chunks = data.split(b"--" + self.boundary)
        for chunk in chunks:
            if len(chunk) == 0:
                pass
            elif len(chunk) == 4:
                self._data_received_part_end()
            else:
                header, p, part = chunk.partition(b"\r\n\r\n")
                if part:
                    if self.ctx.get('name', None):
                        self._data_received_part_end()
                    name, filename, content_type = self.get_name_from_header(header)
                    self.data_received_header(name, filename, content_type)
                    self._data_received_part(part[0:-2])
                else:
                    self._data_received_part(chunk)

    def data_received_header(self, name, filename=None, content_type=None):
        pass

    def data_received_part(self, part):
        pass

    def data_received_part_end(self):
        pass


class MongoUploadHandlerMixin(UploadHandlerMixin):
    filefs = None
    filehandler = None
    def data_received_header(self, name, filename=None, content_type=None):
        self.filehandler = self.filefs.new_file(filename=filename, contentType=content_type)
        self.ctx['fid'] = str(self.filehandler._id)

    def data_received_part(self, part):
        if self.filehandler:
            self.filehandler.write(part)

    def data_received_part_end(self):
        if self.filehandler:
            self.filehandler.close()
            self.filehandler = None


class FileUploadHandlerMixin(UploadHandlerMixin):
    uploadpath = None
    filehandler = None
    def data_received_header(self, name, filename=None, content_type=None):
        if filename:
            if self.uploadpath:
                filepath = self.uploadpath+filename
                self.filehandler = open(filepath, 'w')
                self.ctx['filepath'] = filepath
            else:
                self.filehandler = tempfile.NamedTemporaryFile(delete=False)
                self.ctx['tmpfile'] = self.filehandler.name

    def data_received_part(self, part):
        if self.filehandler:
            self.filehandler.write(part)

    def data_received_part_end(self):
        if self.filehandler:
            self.filehandler.close()
            self.filehandler = None


