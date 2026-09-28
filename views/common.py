import os
import shutil
from pathlib import Path
from uuid import uuid4
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from PIL import Image
from config import IMAGE_DIR, BASE_DIR


class Page(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app

    def button(self, master, text, command, **kwargs):
        button = ctk.CTkButton(master,text=text,command=lambda:self.app.run_action(command),**kwargs)
        button.pack(side="left",padx=4,pady=6)
        return button

    def toolbar(self):
        bar = ctk.CTkFrame(self)
        bar.pack(fill="x",padx=8,pady=4)
        return bar

    def note(self, text):
        ctk.CTkLabel(self,text=text,anchor="w",wraplength=1120,justify="left").pack(fill="x",padx=12,pady=4)


class DataTable(ctk.CTkFrame):
    def __init__(self, master, columns, height=12, on_select=None):
        super().__init__(master)
        self.columns = columns
        self.rows = {}
        self.tree = ttk.Treeview(self,columns=[c[0] for c in columns],show="headings",height=height,selectmode="browse")
        for key,label,width in columns:
            self.tree.heading(key,text=label)
            self.tree.column(key,width=width,minwidth=60,anchor="w")
        y = ttk.Scrollbar(self,orient="vertical",command=self.tree.yview)
        x = ttk.Scrollbar(self,orient="horizontal",command=self.tree.xview)
        self.tree.configure(yscrollcommand=y.set,xscrollcommand=x.set)
        self.tree.grid(row=0,column=0,sticky="nsew")
        y.grid(row=0,column=1,sticky="ns")
        x.grid(row=1,column=0,sticky="ew")
        self.grid_rowconfigure(0,weight=1)
        self.grid_columnconfigure(0,weight=1)
        self.pack(fill="both",expand=True,padx=8,pady=6)
        if on_select:
            self.tree.bind("<<TreeviewSelect>>",lambda event:on_select())

    def load(self, rows):
        self.tree.delete(*self.tree.get_children())
        self.rows.clear()
        for index,row in enumerate(rows):
            key = str(index)
            self.rows[key] = row
            self.tree.insert("","end",iid=key,values=[row.get(c[0],"") if row.get(c[0]) is not None else "" for c in self.columns])

    def selected(self):
        selection = self.tree.selection()
        if not selection:
            raise ValueError("Select a row in the table first.")
        return self.rows[selection[0]]


class FormDialog(ctk.CTkToplevel):
    """Fields: (key, label, initial, choices-or-None, hidden-password)."""
    def __init__(self, app, title, fields, submit, note=""):
        super().__init__(app)
        self.app, self.inputs = app,{}
        self.title(title)
        self.geometry("600x620")
        self.transient(app)
        body = ctk.CTkScrollableFrame(self)
        body.pack(fill="both",expand=True,padx=12,pady=12)
        if note:
            ctk.CTkLabel(body,text=note,wraplength=520,justify="left").pack(pady=6)
        for key,label,initial,choices,hidden in fields:
            ctk.CTkLabel(body,text=label,anchor="w").pack(fill="x",padx=6,pady=(8,0))
            if choices is not None:
                widget = ctk.CTkComboBox(body,values=list(choices) or [""],state="readonly",width=490)
                widget.set(str(initial or (list(choices)[0] if choices else "")))
            else:
                widget = ctk.CTkEntry(body,width=490,show="*" if hidden else "")
                widget.insert(0,str(initial if initial is not None else ""))
            widget.pack(fill="x",padx=6,pady=3)
            self.inputs[key] = widget
        def save():
            submit({key:widget.get() for key,widget in self.inputs.items()})
            self.destroy()
        ctk.CTkButton(self,text="Save / Confirm",command=lambda:app.run_action(save)).pack(pady=8)
        ctk.CTkButton(self,text="Cancel",command=self.destroy).pack(pady=(0,10))
        self.after(150,self._grab)

    def _grab(self):
        if self.winfo_exists():
            self.grab_set()


def field(key, label, initial="", choices=None, hidden=False):
    return key,label,initial,choices,hidden


def info(text):
    messagebox.showinfo("BrewHub",text)


def saved_file(path):
    if messagebox.askyesno("File saved",f"Saved:\n{path}\n\nOpen it now?"):
        if os.name == "nt":
            os.startfile(str(path))
        else:
            info(f"Open this file with your PDF/CSV viewer:\n{path}")


def import_product_image():
    selected = filedialog.askopenfilename(title="Choose a product picture",filetypes=[("Images","*.png *.jpg *.jpeg *.webp")])
    if not selected:
        return None
    IMAGE_DIR.mkdir(parents=True,exist_ok=True)
    # Keep a portable copy, so the original image can be moved afterwards.
    destination = IMAGE_DIR / (uuid4().hex+".png")
    with Image.open(selected) as original:
        original.thumbnail((1600,1600))
        original.convert("RGB").save(destination)
    return destination.relative_to(BASE_DIR).as_posix()

