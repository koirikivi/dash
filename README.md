dash -- Super-minimal process tracking tool

Word of caution: this is very much pre-alpha and work in progress

Example usage:

```bash
$ alias dash=`pwd`/dash.py
$ dash project myproject
$ dash start design
# * design design design *
$ dash end
# * take a break *
$ dash start  # resumes work on last phase, e.g. "design"
# * design design design *
$ dash start code  # end work on design, start work on code
# * hack hack hack *
$ dash end && sleep 600 && dash start  # take a 10 minute break
# * hack hack hack *
$ dash end  # end work
$ dash log  # view work log
```
