import IceStorm
import logging

def get_topic_manager(broker):
    """
    Devuelve un proxy IceStorm TopicManager.
    
    :param broker: Es una instancia de la clase IcePy `Ice.Communicator`. Se utiliza para establecer comunicación con el servicio IceStorm
    :return: Devuelve una instancia de `IceStorm.TopicManagerPrx` o `None`.
    """
    proxy_string = 'IceStorm/TopicManager:tcp -h localhost -p 10000'
    proxy = broker.stringToProxy(proxy_string)
    if proxy is None:
        logging.info("property {} not set".format(proxy_string))
        return None

    logging.info(f"Usando IceStorm en: '{proxy_string}'")
    return IceStorm.TopicManagerPrx.checkedCast(proxy)
