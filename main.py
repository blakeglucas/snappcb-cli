from context import Context, GlobalOptions
from routing import drilling, NccRoutingOptions

test_context = Context(
    'C:/Users/Blake Lucas/Documents/Hardware Projects/ATtiny804USB/ATtiny804USB-F_Cu.gbr',
    'C:/Users/Blake Lucas/Documents/Hardware Projects/ATtiny804USB/ATtiny804USB-B_Cu.gbr',
    'C:/Users/Blake Lucas/Documents/Hardware Projects/ATtiny804USB/ATtiny804USB-Edge_Cuts.gbr',
    'C:/Users/Blake Lucas/Documents/Hardware Projects/ATtiny804USB/ATtiny804USB-PTH.drl',
    options=GlobalOptions(edge_cuts_on_cu=False)
)

def main():
    result = drilling(test_context)

if __name__ == "__main__":
    main()
