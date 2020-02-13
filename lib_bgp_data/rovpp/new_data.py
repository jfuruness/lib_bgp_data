import json

with open("result.json") as j:
    g_dict = json.loads(j.read())
    new_data = {}
    # htype/subtablename/polnum/plane-type/adopting_nonadopting/str(valstrs)
    for pol_num in g_dict["subprefix_hijack"]["rovpp_edge_ases"]:
        if pol_num == "0":
            continue
        else:
            X = [1,10,20,30,40,60,80]
            new_data[pol_num] = {"X": X,
                                 "Y": []}
            adopting_l = g_dict["subprefix_hijack"]["rovpp_edge_ases"][pol_num]["data"]["_adopting"]["['trace_hijacked', 'trace_preventivehijacked']"]["Y"]
            collateral_l = g_dict["subprefix_hijack"]["rovpp_edge_ases"][pol_num]["data"]["_collateral"]["['trace_hijacked', 'trace_preventivehijacked']"]["Y"]
            # Collateral starts at 0but adopting doesn't so start at 1
            for adopt_perc, adopting_h, collateral_h in zip(X, adopting_l, collateral_l):
                new_data[pol_num]["Y"].append(adopting_h * adopt_perc / 100 + collateral_h * (1 - (adopt_perc / 100)))
    from pprint import pprint
#    pprint(new_data)

    import matplotlib.pyplot as plt
#    plt.set_ylim(0,100)
    styles = ["-", "--", "-.", ":", "solid", "dotted", "dashdot", "dashed"]
    markers = [".", "1", "*", "x", "d", "2", "3", "4"]
    plt.xlabel("% adoption")
    plt.ylabel("Data plane % Hijacked")
    plt.plot(X, new_data["1"]["Y"], label="ROV", ls=styles[int(1)], marker=markers[int(1)])
    plt.plot(X, new_data["2"]["Y"], label="ROV++v1", ls=styles[int(2)], marker=markers[int(2)])
    plt.plot(X, new_data["5"]["Y"], label="ROV++v2", ls=styles[int(5)], marker=markers[int(5)])
#    plt.plot(X, new_data["3"]["Y"], label="ROV++v2a", ls=styles[int(3)], marker=markers[int(3)])
    plt.plot(X, new_data["4"]["Y"], label="ROV++v3", ls=styles[int(4)], marker=markers[int(4)])

    plt.legend(loc="lower left")

    plt.show()
        
        
