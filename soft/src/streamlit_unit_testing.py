import streamlit as st
import lib_helpers as hlp
import drv_usspi
import drv_lit3rick
import lib_ultrasound as uslib

"# ELK libraries unit testing"

"## `drv_usspi.py` : US-SPI driver "
"`.params_desc` ->"
st.table(drv_usspi.params_desc)
"`.raw_params` ->"
st.table(drv_usspi.raw_params) 

"## `drv_lit3rick.py` : Lit3rick driver"
"`.params_desc` ->"
st.table(drv_lit3rick.params_desc)
"`.raw_params` ->"
st.table(drv_lit3rick.raw_params)


"## `lib_ultrasound.py` : Main ultrasound library"
a_card_name = st.selectbox( "Choose the US card connected:", uslib.get_card_names())
"`.install(a_card_name)` ->"
st.write(uslib.install(a_card_name))
"`.get_card_name()` ->"
st.write("Active US Card : " + uslib.get_card_name())

"### Current params values"
"`.get_raw_params()` ->"
st.table(uslib.get_raw_params())
