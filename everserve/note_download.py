from evernote.api.client import EvernoteClient
# Prod vincent@khougaz.com
# dev_token = "S=s462:U=4e5f584:E=1548920f811:C=14d316fc898:P=1cd:A=en-devtoken:V=2:H=8faad950655d66dfe20808c9c7caa275"
# Dev vincent@khougaz.com
dev_token = "S=s1:U=90cdf:E=1548935fe87:C=14d3184cf68:P=1cd:A=en-devtoken:V=2:H=7369fbadab16c3aee7127e04368ac34f"

client = EvernoteClient(token=dev_token)

def get_notebooks():
    client = EvernoteClient(token=dev_token)
    noteStore = client.get_note_store()
    return noteStore.listNotebooks()

print(get_notebooks())