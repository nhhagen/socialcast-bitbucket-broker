"""
Stand-in class for bitbucket's BaseBroker.
"""
class BaseBroker():
        def get_local(self, arg, theclass):
                return theclass()