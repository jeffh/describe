import nose
from describe.nose_plugin import SpecPlugin

def run():
    import sys
    nose.main(argv=['-s'], addplugins=[SpecPlugin()])
                
if __name__ == '__main__':
    run()