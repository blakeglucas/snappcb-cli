from context import Context, GlobalOptions
from routing import ncc_routing, NccRoutingOptions

test_context = Context(
    'C:/Users/Blake Lucas/Documents/Hardware Projects/ATtiny804USB/ATtiny804USB-F_Cu.gbr',
    'C:/Users/Blake Lucas/Documents/Hardware Projects/ATtiny804USB/ATtiny804USB-B_Cu.gbr',
    'C:/Users/Blake Lucas/Documents/Hardware Projects/ATtiny804USB/ATtiny804USB-Edge_Cuts.gbr',
    options=GlobalOptions(edge_cuts_on_cu=False)
)

def main():
    result = ncc_routing(test_context, options=NccRoutingOptions(direction='vertical'))
    test_context.generate_svg(result.fcu, 'test_fcu.svg')
    test_context.generate_svg(result.bcu, 'test_bcu.svg')
    test_context.generate_svg(result.edge_cuts_raw, 'test_ecr.svg')
    test_context.generate_svg(result.edge_cuts, 'test_ec.svg')

if __name__ == "__main__":
    main()
