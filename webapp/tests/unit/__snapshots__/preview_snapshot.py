'''
simple script to convert jest snapshot into html file that can be viewed in a browser. 

currently only works if snap file contains only a single snapshot
'''


def main(snapshot_filename, template_filename="snapshot_template.html"):
    with open(snapshot_filename, 'r') as f:
        snapshot="".join(f.readlines()[4:-1])

    with open(template_filename, 'r') as f:
        template = f.read()

    with open(snapshot_filename+".html", 'w') as f:
        f.write(template.format(snapshot))
    



if __name__ == "__main__":
    import plac; plac.call(main)
