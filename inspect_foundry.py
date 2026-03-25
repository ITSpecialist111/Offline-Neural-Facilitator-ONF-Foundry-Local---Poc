
try:
    from foundry_local import FoundryLocalManager
    print("FoundryLocalManager imported successfully")
    print(dir(FoundryLocalManager))
    
    # Try to instantiate?
    # mgr = FoundryLocalManager()
    # print(mgr)
except Exception as e:
    print(e)
