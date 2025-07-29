import asyncio

from tools import (
    hackerNews_item,
    hackerNews_user,
    hackerNews_maxitem,
    hackerNews_updates_ids,
    hackerNews_showstories_ids,
    hackerNews_beststories_ids,
    hackerNews_newstories_ids,
    hackerNews_jobstories_ids,
    hackerNews_askstories_ids,
    hackerNews_topstories_ids,
    hackerNews_askstories,
    hackerNews_jobstories,
    hackerNews_showstories,
    hackerNews_updates,
    hackerNews_topstories,
    hackerNews_newstories,
    hackerNews_beststories
)

async def main():
    print('Updates IDs:', await hackerNews_updates_ids())
    print("")
    print('Showstories IDs:', await hackerNews_showstories_ids())
    print("")
    print('Beststories IDs:', await hackerNews_beststories_ids())
    print("")
    print('Newstories IDs:', await hackerNews_newstories_ids())
    print("")
    print('Jobstories IDs:', await hackerNews_jobstories_ids())
    print("")
    print('Askstories IDs:', await hackerNews_askstories_ids())
    print("")
    print('Topstories IDs:', await hackerNews_topstories_ids())
    print("")
    print("")

    print('Updates:', await hackerNews_updates(1))
    print("")
    print('Askstories:', await hackerNews_askstories(1))
    print("")
    print('Jobstories:', await hackerNews_jobstories(1))
    print("")
    print('Showstories:', await hackerNews_showstories(1))
    print("")
    print('Topstories:', await hackerNews_topstories(1))
    print("")
    print('Newstories:', await hackerNews_newstories(1))
    print("")
    print('Beststories:', await hackerNews_beststories(1))
    print("")
    print("")

    print('Single Item:', await hackerNews_item(44721599))
    print("")
    print('Single User:', await hackerNews_user('westpfelia'))
    print("")
    print('Max Item:', await hackerNews_maxitem())


if __name__ == "__main__":
    asyncio.run(main())

