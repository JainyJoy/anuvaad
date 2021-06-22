import os
import subprocess

from anuvaad_auditor import log_info


class PdfToHtml(object):
    def __init__(self, input_filename):
        self.file_name_without_ext = os.path.splitext(input_filename)[0]

    def get_new_html_file_name(self):
        return os.path.join(self.file_name_without_ext + '-html.html')

    def get_new_html_file_path(self, html_output_dir, generated_html_file_name):
        directory, file_name = os.path.split(html_output_dir)
        return os.path.join(directory, generated_html_file_name)

    # Usage: pdftohtml [options] <PDF-file> [<html-file> <xml-file>]
    def convert_pdf_to_html(self, input_pdf_file_path, html_output_dir, timeout=None):
        args = ['pdftohtml', '-s', input_pdf_file_path, html_output_dir]
        log_info("convert_pdf_to_html:: PDF to HTML conversion process STARTED.", None)
        process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        log_info("convert_pdf_to_html:: PDF to HTML conversion process ENDED.", None)

        generated_html_file_name = self.get_new_html_file_name()
        generated_html_file_path = self.get_new_html_file_path(html_output_dir=html_output_dir,
                                                               generated_html_file_name=generated_html_file_name)
        log_info(f"convert_pdf_to_html:: Generated html file path: {generated_html_file_path}", None)
        return generated_html_file_path
