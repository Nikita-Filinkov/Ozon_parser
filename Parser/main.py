from parser import FullPower

link = (
    'https://www.ozon.ru/product/mayka-tvoe-bazovaya-760627363/?asb2=k0ONg4Icz76KVGs-hDCr1l76e8IqxWcYGJjJ2ZxmijAgBwN'
    '4ivLbRBzCiYAm0vSGn5IfMlrfv15v7BGF53ycBw&from_sku=760626422&oos_search=false')

if __name__ == '__main__':
    """
    Основная точка входа в программу. Создает и запускает экземпляр FullPower для парсинга данных.
    """
    writer = FullPower(link=link)
    writer.run()