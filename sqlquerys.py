

def check_in_base(code_list):
    string = ""
    for code in code_list:
        string += f"('{code}'),"
    string = string[:-1]

    return f"""
SET NOCOUNT ON
create table #temp1 (itemno varchar(20))
insert into #temp1 
values {string}
update #temp1
set itemno=rtrim(replace(itemno, char(160), char(32)))

select t.itemno from #temp1 t
left join item i on i.ITEMNO=t.itemno and i.SUPLNO='vw'
where isnull(i.itemno,'')=''
drop table #temp1"""


def check_itemno(ordeno, orrwid):
    return f"""SELECT TOP 1 LEFT(ITEMNO, 14) as ITEMNO
                             FROM ORRWS01
WHERE ordeno = {ordeno} and orrwid = {orrwid}"""