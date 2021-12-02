"""
Fully extracts each DLM from unencrypted Xerox upgrade files (.zip)
i.e WorkCentre_7830-35_Manual_Upgrade.zip
Adin Drabkin - abd5264 [at] rit.edu
"""

import os
import click
import tarfile
import zipfile
import io

class DLM_Ripper():
    XZ_HEADER = b"\xFD\x37\x7A\x58\x5A\x00"  # standard tar.gz header
    XRX_END = b"\x25\x25\x58\x52\x58\x65\x6E\x64\x0A"  # %%XRXend 


    def fix_xz(self, root_dir, file_path):
        """
        fix and extract an obfuscated xz file to ./:root_dir:/
        """
        with open(file_path, 'rb') as original_file:
            # try to locate the end of the xerox header
            split_content = original_file.read(100).split(self.XZ_HEADER, 1)
            if len(split_content) != 2:
                return False
            # combine file header and content
            fixed_content = io.BytesIO(self.XZ_HEADER + split_content[-1] + original_file.read())

            tarball = tarfile.open(fileobj=fixed_content, mode='r:xz', errorlevel=1)
            for file_ in tarball:
                try:
                    tarball.extract(file_, path=root_dir)
                except:  # skip failed files
                    continue


    def fix_extract_xz_dir(self, dir):
        """
        have self.fix_xz extract all files in :dir: to dir/root/
        """
        root_dir = os.path.join(dir, "root")
        print(f"[+] Attempting to extract xz files in {dir}")
        for entry in os.listdir(dir):
            # skip directory files and files not ending in a digit
            if (os.path.isdir(entry)) or (not entry.split(".")[-1].isdigit()):
                continue
            entry_fullname = os.path.join(dir, entry)
            self.fix_xz(root_dir, entry_fullname)
        print(f"[+] Extracted xz files in {dir}")
        

    def fix_extract_dlm(self, dlm_path):
        """
        Fix and extract DLM files. Very memory intensive.
        """
        print(f'[+] Attempting to fix DLM file {dlm_path.split(os.pathsep)[-1]}')
        with open(dlm_path, 'rb') as original_file:
            split_content = original_file.read(4000).split(self.XRX_END, 1)
            if len(split_content) != 2:
                print(f"[!] Unable to locate the gzip header for {original_file}")
                return False
            print(f"[+] Located the beginning of gzip file {dlm_path.split(os.pathsep)[-1]}")

            # base name without file extension
            base_name = ".".join(dlm_path.split(".")[:-1])

            if os.path.exists(base_name):
                print(f'[!] already exists, skipping {base_name}')
                return

            dlm_fixed_content = split_content[-1] + original_file.read()
        try:
            tarball = tarfile.open(fileobj=io.BytesIO(dlm_fixed_content), mode='r:gz', errorlevel=1)
        except:
            return 

        for file_ in tarball:
            try:
                tarball.extract(file_, path=base_name)
            except:
                continue
        print(f"[+] Extracted {base_name}")
        return base_name


    def fix_full(self, zip_path):
        """
        unzip firmware file, extract all DLMs, fix each extracted DLM folder.
        """
        # assumes a single file exists at level 1 of the zipfile, being the zipfile without ".zip"
        dlm_files = []
        with zipfile.ZipFile(zip_path) as zf:
            for x in zf.namelist():
                if x.split(".")[-1].lower() == "dlm":
                    dlm_files.append(x)
            zf.extractall()
        # extract each DLM file
        for x in dlm_files:
            if extracted_dlm := self.fix_extract_dlm(x):
                self.fix_extract_xz_dir(extracted_dlm)
        print(f"[+] Finished extracting DLMs")


@click.group()
def cli():
    pass


@cli.command("xzdir")
@click.argument('directory', type=click.Path(exists=True))
def main_combined(directory):
    """
    Deobfuscate and unzip a directory containing obfuscated xz files
    """
    xz_fixer = DLM_Ripper()
    xz_fixer.fix_extract_xz_dir(directory)

@cli.command("full")
@click.argument('firmware_zip', type=click.Path(exists=True))
def main_full(firmware_zip):
    """
    Unzip and fully extract unencrypted Xerox firmware
    """
    xz_fixer = DLM_Ripper()
    xz_fixer.fix_full(firmware_zip)


if __name__ == '__main__':
    cli()
