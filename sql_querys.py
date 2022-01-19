
def check_itemno(ordeno, orrwid):
    return f"""SELECT TOP 1 LEFT(ITEMNO, 14) as ITEMNO
                             FROM ORRWS01
WHERE ordeno = {ordeno} and orrwid = {orrwid}"""