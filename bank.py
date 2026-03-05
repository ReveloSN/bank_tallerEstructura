# ============================================
# BANKING TRANSACTION ENGINE
# Data Structures: Queue (deque), Stack, Array
# ============================================

import tkinter as tk
from tkinter import messagebox, ttk
from collections import deque
from datetime import datetime


# ============================================
# UI THEME  (patron: centralizacion de estilos)
# ============================================

T = {
    "bg":      "#e8f0fe",
    "white":   "#ffffff",
    "panel":   "#dce8fd",
    "accent":  "#1a56db",
    "accent2": "#1e40af",
    "success": "#1d6f42",
    "error":   "#b91c1c",
    "warn":    "#1d4ed8",
    "text":    "#1e293b",
    "muted":   "#475569",
    "border":  "#bfdbfe",
    "fn":      "Segoe UI",
}

def lbl(parent, text, size=9, bold=False, color=None, **kw):
    return tk.Label(parent, text=text, bg=kw.pop("bg", T["white"]),
                    fg=color or T["text"],
                    font=(T["fn"], size, "bold" if bold else "normal"), **kw)

def btn(parent, text, cmd, bg=None, fg="white", size=10, bold=False, pady=7):
    return tk.Button(parent, text=text, command=cmd,
                    bg=bg or T["accent"], fg=fg,
                    activebackground=T["accent2"], activeforeground="white",
                    font=(T["fn"], size, "bold" if bold else "normal"),
                    relief="flat", cursor="hand2", pady=pady)

def sep(parent, color=None):
    tk.Frame(parent, bg=color or T["border"], height=1).pack(fill="x", pady=12)

def card(parent, **kw):
    return tk.Frame(parent, bg=T["white"], padx=20, pady=20,
                    highlightbackground=T["border"], highlightthickness=1, **kw)


# ============================================
# CLASS: BankAccount
# ============================================

class BankAccount:

    def __init__(self, number, balance):
        self._number  = number
        self._balance = balance

    def get_number(self):  return self._number
    def get_balance(self): return self._balance

    def deposit(self, amount):
        self._balance += amount

    def withdraw(self, amount):
        if self._balance >= amount:
            self._balance -= amount
            return True
        return False


# ============================================
# CLASS: TransactionEngine
# ============================================

class TransactionEngine:

    def __init__(self):
        self.queue  = deque()
        self.stack  = []
        self.failed = []
        self.log    = []
        self.MAX_FAILED = 5
        self.accounts = {
            "1001": BankAccount("1001", 500),
            "1002": BankAccount("1002", 800),
            "1003": BankAccount("1003", 1200),
        }

    def enqueue(self, origin, destination, amount):
        self.queue.append((origin, destination, amount))

    def process_next(self):
        if not self.queue:
            return None
        origin, destination, amount = self.queue.popleft()
        time = datetime.now().strftime("%H:%M:%S")
        try:
            if origin not in self.accounts or destination not in self.accounts:
                raise Exception("Cuenta invalida")
            self.stack.append("validation")
            if not self.accounts[origin].withdraw(amount):
                raise Exception("Fondos insuficientes")
            self.stack.append("withdraw")
            self.accounts[destination].deposit(amount)
            self.stack.append("deposit")
            self.stack.clear()
            entry = (time, origin, destination, f"${amount:,.2f}", "OK")
            self.log.append(entry)
            return ("ok", entry)
        except Exception as e:
            self._rollback(origin, destination, amount)
            if len(self.failed) >= self.MAX_FAILED:
                self.failed.pop(0)
            self.failed.append((origin, destination, amount))
            entry = (time, origin, destination, f"${amount:,.2f}", str(e))
            self.log.append(entry)
            return ("error", entry)

    def _rollback(self, origin, destination, amount):
        while self.stack:
            op = self.stack.pop()
            if op == "withdraw": self.accounts[origin].deposit(amount)
            if op == "deposit":  self.accounts[destination].withdraw(amount)

    def get_accounts(self):            return self.accounts
    def get_failed_transactions(self): return self.failed
    def get_log(self):                 return self.log
    def queue_size(self):              return len(self.queue)
    def queue_snapshot(self):          return list(self.queue)


# ============================================
# CLASS: Interface
# ============================================

class Interface:

    def __init__(self, engine):
        self.engine = engine
        self.paused = False
        self.window = tk.Tk()
        self.window.title("Motor de Transacciones Bancarias")
        self.window.configure(bg=T["bg"])
        self.window.resizable(False, False)
        self._build()
        self._poll()
        self.window.mainloop()

    def _build(self):
        main = tk.Frame(self.window, bg=T["bg"])
        main.pack(padx=20, pady=20)
        self._build_form(main)
        self._build_right(main)

    # ---- FORMULARIO ----
    def _build_form(self, parent):
        c = card(parent)
        c.grid(row=0, column=0, padx=(0, 16), sticky="n")

        lbl(c, "Nueva Transaccion", 13, bold=True).pack(anchor="w")
        lbl(c, "Transfiere entre cuentas disponibles", color=T["muted"]).pack(anchor="w", pady=(2, 14))

        self.origin      = self._entry(c, "Cuenta Origen")
        self.destination = self._entry(c, "Cuenta Destino")
        self.amount      = self._entry(c, "Monto ($)")

        lbl(c, "Cuentas: 1001  1002  1003", 8, color=T["muted"]).pack(anchor="w", pady=(2, 10))
        btn(c, "Enviar Transaccion", self.create_transaction, bold=True).pack(fill="x")
        sep(c)

        self.pause_btn = btn(c, "Pausar Servidor", self.toggle_pause, bg=T["warn"])
        self.pause_btn.pack(fill="x")
        sep(c)

        row = tk.Frame(c, bg=T["white"])
        row.pack(fill="x")
        btn(row, "Ver Cuentas",  self.view_accounts,  bg=T["panel"], fg=T["text"], size=9).pack(side="left", padx=(0,6), fill="x", expand=True)
        btn(row, "Ver Fallidas", self.view_failed,    bg=T["panel"], fg=T["text"], size=9).pack(side="left", fill="x", expand=True)

        self.status_var = tk.StringVar(value="Sistema listo.")
        tk.Label(c, textvariable=self.status_var, font=(T["fn"], 8),
                bg=T["white"], fg=T["muted"]).pack(anchor="w", pady=(10, 0))

    # ---- PANEL DERECHO ----
    def _build_right(self, parent):
        right = tk.Frame(parent, bg=T["white"],
                        highlightbackground=T["border"], highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew")

        # Cola
        qh = tk.Frame(right, bg=T["panel"], padx=14, pady=10)
        qh.pack(fill="x")
        lbl(qh, "Cola en espera", 11, bold=True, bg=T["panel"], color=T["accent"]).pack(side="left")
        self.queue_count = tk.StringVar(value="0 transacciones")
        tk.Label(qh, textvariable=self.queue_count, font=(T["fn"], 9),
                bg=T["panel"], fg=T["muted"]).pack(side="right")

        tk.Frame(right, bg=T["border"], height=1).pack(fill="x")

        self.queue_list = tk.Listbox(right, font=(T["fn"], 9),
                                    bg=T["bg"], fg=T["text"],
                                    selectbackground=T["accent"],
                                    relief="flat", height=5, highlightthickness=0)
        self.queue_list.pack(fill="x", padx=8, pady=8)

        tk.Frame(right, bg=T["border"], height=1).pack(fill="x")

        # Registro
        lh = tk.Frame(right, bg=T["white"], padx=14, pady=10)
        lh.pack(fill="x")
        lbl(lh, "Registro", 12, bold=True).pack(side="left")
        btn(lh, "Ver completo", self.view_log_window, bg=T["bg"], fg=T["accent"], size=8, pady=3).pack(side="right")

        tk.Frame(right, bg=T["border"], height=1).pack(fill="x")

        style = ttk.Style()
        style.configure("Log.Treeview", font=(T["fn"], 9), rowheight=26,
                        background=T["white"], fieldbackground=T["white"], foreground=T["text"])
        style.configure("Log.Treeview.Heading", font=(T["fn"], 9, "bold"),
                        background=T["bg"], foreground=T["muted"])
        style.layout("Log.Treeview", [("Log.Treeview.treearea", {"sticky": "nswe"})])

        cols = ("Hora", "De", "A", "Monto", "Estado")
        self.tree = ttk.Treeview(right, columns=cols, show="headings",
                                style="Log.Treeview", height=8)
        for col, w in zip(cols, [60, 55, 55, 75, 90]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.tag_configure("ok",  foreground=T["success"])
        self.tree.tag_configure("err", foreground=T["error"])
        self.tree.pack(padx=8, pady=8)

    # ---- HELPERS ----
    def _entry(self, parent, label):
        lbl(parent, label, 9, color=T["muted"], anchor="w").pack(fill="x")
        e = tk.Entry(parent, font=(T["fn"], 10), bg=T["bg"], fg=T["text"],
                    relief="flat", highlightbackground=T["border"],
                    highlightthickness=1, insertbackground=T["accent"])
        e.pack(fill="x", ipady=6, pady=(2, 10))
        return e

    def _add_to_tree(self, entry):
        tag = "ok" if entry[4] == "OK" else "err"
        self.tree.insert("", 0, values=entry, tags=(tag,))
        rows = self.tree.get_children()
        if len(rows) > 10:
            self.tree.delete(rows[-1])

    def _refresh_queue(self):
        self.queue_list.delete(0, tk.END)
        snap = self.engine.queue_snapshot()
        self.queue_count.set(f"{len(snap)} transaccion(es)")
        for i, (o, d, a) in enumerate(snap):
            self.queue_list.insert(tk.END, f"  #{i+1}  {o} -> {d}   ${a:,.2f}")
        if not snap:
            self.queue_list.insert(tk.END, "  Cola vacia")

    def _popup(self, title, build_fn):
        win = tk.Toplevel(self.window)
        win.title(title)
        win.configure(bg=T["white"])
        win.resizable(False, False)
        build_fn(win)

    # ---- PAUSA ----
    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.pause_btn.config(text="Reanudar Servidor", bg=T["success"])
            self.status_var.set("Servidor pausado - transacciones encoladas.")
        else:
            self.pause_btn.config(text="Pausar Servidor", bg=T["warn"])
            self.status_var.set("Servidor reanudado - procesando cola...")

    # ---- POLL LOOP ----
    def _poll(self):
        if not self.paused and self.engine.queue_size() > 0:
            result, entry = self.engine.process_next()
            self._add_to_tree(entry)
            self.status_var.set(f"{'Procesado' if result == 'ok' else 'Fallido'}: {entry[1]} -> {entry[2]}  {entry[3]}")
        self._refresh_queue()
        self.window.after(800, self._poll)

    # ---- ACCIONES ----
    def create_transaction(self):
        origin, destination = self.origin.get().strip(), self.destination.get().strip()
        try:
            amount = float(self.amount.get())
            if amount <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Ingresa un monto valido mayor a 0.")
            return
        self._popup("Confirmar Transaccion", lambda w: self._build_confirm(w, origin, destination, amount))

    def _build_confirm(self, win, origin, destination, amount):
        win.geometry("300x230")
        lbl(win, "Confirmar Transaccion", 13, bold=True).pack(pady=(20, 12))
        for label, val in [("De:", origin), ("A:", destination), ("Monto:", f"${amount:,.2f}")]:
            row = tk.Frame(win, bg=T["white"])
            row.pack(pady=3)
            lbl(row, label, 9, color=T["muted"], width=8, anchor="e").pack(side="left")
            lbl(row, val, 10, bold=True).pack(side="left")
        btns = tk.Frame(win, bg=T["white"])
        btns.pack(pady=20)
        btn(btns, "Confirmar", lambda: [win.destroy(), self._enqueue(origin, destination, amount)],
            bold=True).pack(side="left", padx=6)
        btn(btns, "Cancelar", win.destroy, bg=T["bg"], fg=T["muted"]).pack(side="left")

    def _enqueue(self, origin, destination, amount):
        self.engine.enqueue(origin, destination, amount)
        self.status_var.set(f"{'Encolado' if self.paused else 'Enviado'}: {origin} -> {destination}  ${amount:,.2f}")
        self._refresh_queue()

    def view_accounts(self):
        def build(win):
            win.geometry("260x200")
            lbl(win, "Estado de Cuentas", 12, bold=True).pack(pady=(16, 10))
            for acc in self.engine.get_accounts().values():
                row = tk.Frame(win, bg=T["bg"], padx=14, pady=8)
                row.pack(fill="x", padx=16, pady=3)
                lbl(row, f"Cuenta {acc.get_number()}", bg=T["bg"]).pack(side="left")
                lbl(row, f"${acc.get_balance():,.2f}", bold=True, color=T["accent"], bg=T["bg"]).pack(side="right")
        self._popup("Estado de Cuentas", build)

    def view_failed(self):
        def build(win):
            win.geometry("320x220")
            lbl(win, "Transacciones Fallidas", 12, bold=True).pack(pady=(16, 10))
            failed = self.engine.get_failed_transactions()
            if not failed:
                lbl(win, "Sin transacciones fallidas", color=T["success"]).pack()
                return
            for o, d, a in failed:
                row = tk.Frame(win, bg=T["panel"], padx=12, pady=6)
                row.pack(fill="x", padx=16, pady=2)
                lbl(row, f"{o} -> {d}", 9, bg=T["panel"]).pack(side="left")
                lbl(row, f"${a:,.2f}", 9, bold=True, color=T["error"], bg=T["panel"]).pack(side="right")
        self._popup("Transacciones Fallidas", build)

    def view_log_window(self):
        def build(win):
            win.geometry("500x360")
            lbl(win, "Registro Completo", 12, bold=True).pack(pady=(16, 10))
            tree = ttk.Treeview(win, columns=("Hora","De","A","Monto","Estado"),
                                show="headings", style="Log.Treeview", height=12)
            for col, w in zip(("Hora","De","A","Monto","Estado"), [70,70,70,90,150]):
                tree.heading(col, text=col)
                tree.column(col, width=w, anchor="center")
            tree.tag_configure("ok",  foreground=T["success"])
            tree.tag_configure("err", foreground=T["error"])
            for entry in reversed(self.engine.get_log()):
                tree.insert("", "end", values=entry, tags=("ok" if entry[4] == "OK" else "err",))
            tree.pack(padx=16, pady=8)
        self._popup("Registro Completo", build)


# ============================================
# MAIN
# ============================================

engine = TransactionEngine()
Interface(engine)