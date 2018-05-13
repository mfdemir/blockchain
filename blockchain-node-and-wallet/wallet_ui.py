from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import wallet

top = Tk()
top.title('Wallet')
top.geometry('600x300')

your_public_key = StringVar()
your_private_key = StringVar()
to_public_key = StringVar()
amount = DoubleVar()


def create_wallet():
    f = filedialog.asksaveasfile(title='Save your generated credentials', mode='w', defaultextension=".txt")
    if f is not None:
        private, public = wallet.generate_ECDSA_keys(f.name)
        your_private_key.set(private)
        your_public_key.set(public)
        label_your_balance.config(text='Your Balance: 0')
    else:
        messagebox.showinfo("Error", "You need to select a file to save your credentials.")


def load_wallet():
    f = filedialog.askopenfile(title='Locate the file that generated previously', mode='r', defaultextension='.txt')
    if f is not None:
        with open(f.name, 'r') as file:
            content = file.read()
            content = content.split('\n')
            private_key = None
            public_key = None
            for line in content:
                if line[:12] == 'private_key:':
                    private_key = line[12:]
                elif line[:11] == 'public_key:':
                    public_key = line[11:]
            if private_key is None or public_key is None:
                messagebox.showinfo("Error", "File is not a wallet information file or is corrupt.")
                return
            your_public_key.set(public_key)
            your_private_key.set(private_key)
            get_balance()


def make_transaction():
    results = wallet.send_transaction(your_public_key.get(), your_private_key.get(), to_public_key.get(), amount.get())
    if results is None:
        messagebox.showinfo("Error", "Unknown error")
        return

    text = ''
    for result in results:
        if 'message' in result:
            text += f'{result["message"]}\n'
        else:
            text += f'???\n'
    messagebox.showinfo("Response", text)
    get_balance()


def get_balance():
    label_your_balance.config(text=f'Your Balance: {wallet.get_balance(your_public_key.get())}')


label_your_balance = Label(top, text='Your Balance: ???', fg='green', font=("Helvetica", 16))
label_your_balance.pack()
button_refresh_balance = Button(top, text="Refresh Balance", command=get_balance).pack()
button_generate_wallet = Button(top, text="Generate a New Wallet", command=create_wallet).pack()
button_load_wallet = Button(top, text='Load Wallet From a Generated File', command=load_wallet).pack()
label_public_key = Label(top, text='Your Public Key')
entry_public_key = Entry(top, textvariable=your_public_key, width=200)
label_private_key = Label(top, text='Your Private Key')
entry_private_key = Entry(top, textvariable=your_private_key, width=200)
label_to_key = Label(top, text='Public Key of Recipient')
entry_to_key = Entry(top, textvariable=to_public_key, width=200)
label_amount = Label(top, text='Amount')
entry_amount = Entry(top, textvariable=amount, width=200)
button_test = Button(top, text="Send", command=make_transaction)

label_public_key.pack()
entry_public_key.pack()
label_private_key.pack()
entry_private_key.pack()
label_to_key.pack()
entry_to_key.pack()
label_amount.pack()
entry_amount.pack()
button_test.pack()

top.mainloop()
