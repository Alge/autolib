import autolib

from pprint import pprint

def test_module_namespace_injection():

    assert "addTwoNumbers" not in dir(autolib)
    autolib.addTwoNumbers(1,3)
    assert "addTwoNumbers" in dir(autolib)
    assert autolib.addTwoNumbers(5, 6) == 11

