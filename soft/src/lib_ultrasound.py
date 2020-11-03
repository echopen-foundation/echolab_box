
import lib_helpers as hlp

g_card_names = ("No card", "US-SPI (Lecoeur)", "Lit3rick (Kelu)", "US-echOpen (echOpen)")
NO_CARD    = 0
US_SPI     = 1
LIT3RICK   = 2
US_ECHOPEN = 3

g_us_card = NO_CARD
drv = None

#----------------------------------------
def install(us_card):
    global g_us_card, drv

    if isinstance(us_card, str):
        us_card = g_card_names.index(us_card)

    g_us_card = us_card
    ret= True
    if g_us_card == US_SPI :
        import drv_usspi     as drv

    elif g_us_card == LIT3RICK :
        import drv_lit3rick  as drv

    elif g_us_card == US_ECHOPEN :
        #import drv_usechopen as drv
        import drv_usspi     as drv       # /!\ TODO US_ECHOPEN not yet implemented

    else:
        drv = None
        g_us_card = NO_CARD
        ret = False

    return ret


#----------------------------------------
def get_card_names():

    return g_card_names

#----------------------------------------
def get_card_name():

    return g_card_names[g_us_card]

#----------------------------------------
def get_params_desc():

    return drv.params_desc
    
#----------------------------------------
def get_raw_params():

    return drv.raw_params