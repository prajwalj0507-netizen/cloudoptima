import sys
try:
    import win32com.client
    ppt = win32com.client.Dispatch("PowerPoint.Application")
    pres = ppt.Presentations.Open(sys.argv[1], ReadOnly=1)
    print("Opened successfully with PowerPoint!")
    pres.Close()
    ppt.Quit()
except Exception as e:
    print(f"Error: {e}")
