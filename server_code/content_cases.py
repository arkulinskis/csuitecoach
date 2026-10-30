"""The Casebook: real, publicly reported situations that executives faced, with the lesson each one teaches.

Facts here were checked against public reporting (see `sources`) in Oct 2026. Keep claims modest: where
sources disagree (numbers, exact quotes), say "about" or leave the detail out. tone: exemplary | cautionary | mixed.
"""

CASES = [
    {
        "id": "tylenol", "company": "Johnson & Johnson", "year": "1982", "role": "CEO", "tone": "exemplary",
        "title": "The Tylenol recall",
        "summary": "Seven people died after taking cyanide-laced Tylenol capsules in the Chicago area. CEO James Burke pulled the product nationwide.",
        "story": [
            "In the autumn of 1982, seven people in the Chicago area died after taking Extra-Strength Tylenol capsules that someone had laced with cyanide. The tampering happened after the product left the factory, and only a small number of bottles were affected.",
            "Johnson & Johnson's chairman, James Burke, chose a nationwide recall rather than a local one, at a cost commonly put at about $100 million, and warned the public not to take the capsules. The company later relaunched Tylenol in tamper-resistant packaging.",
            "Burke credited the company's Credo, which puts customers first, then employees, communities and finally shareholders, with giving him the backing to spend that money. Tylenol won back much of its market share within about a year, and the case became the standard business-school example of crisis leadership.",
        ],
        "lesson": "When people are at risk, act on your stated values before you have all the facts, and be visibly on the side of the public.",
        "sources": [("Knowledge at Wharton: Tylenol and the legacy of J&J's James Burke", "https://knowledge.wharton.upenn.edu/article/tylenol-and-the-legacy-of-jjs-james-burke/")],
    },
    {
        "id": "redslide", "company": "Ford Motor Company", "year": "2006", "role": "CEO / COO", "tone": "exemplary",
        "title": "The first red slide",
        "summary": "Every status chart at Alan Mulally's weekly review was green while Ford headed for a huge loss. When Mark Fields showed red, Mulally clapped.",
        "story": [
            "Alan Mulally joined Ford as CEO in 2006 and ran a weekly Business Plan Review in which every executive colour-coded their projects green, yellow or red. Week after week the charts were green, while Ford's automotive business was on its way to losing billions that year.",
            "Mark Fields, then head of the Americas, finally showed a red: a launch held up by a problem with the vehicle. The room tensed. Mulally applauded, thanked him for the visibility and asked who could help. Within weeks the charts became honest.",
            "Fields was not punished: he later became chief operating officer and, in 2014, Mulally's successor as CEO.",
        ],
        "lesson": "People copy how the leader reacts to the first piece of bad news. Reward the messenger and you get the truth early, while it is still cheap to fix.",
        "sources": [("Bloomberg: Ford's slow-motion CEO succession plan (2012)", "https://www.bloomberg.com/news/articles/2012-11-15/fords-slow-motion-ceo-succession-plan")],
    },
    {
        "id": "intelmemory", "company": "Intel", "year": "1985", "role": "CEO", "tone": "exemplary",
        "title": "Walking out the door and coming back in",
        "summary": "Andy Grove asked Gordon Moore what a new CEO would do with the failing memory business. Then they did it themselves.",
        "story": [
            "In the mid-1980s Intel's founding business, memory chips, was being overrun by Japanese competitors. Andy Grove asked Gordon Moore what a new CEO brought in by the board would do. Moore said he would get out of memories.",
            "Grove's reply, as he told it in Only the Paranoid Survive: why shouldn't you and I walk out the door, come back and do it ourselves? Intel left the memory business, cut deeply, and bet the company on microprocessors.",
        ],
        "lesson": "Look at your business the way an outsider with no history would. Identity and past success are the hardest things to let go of.",
        "sources": [("NPR: Intel legends Moore and Grove (2012)", "https://www.npr.org/2012/04/06/150057676/intel-legends-moore-and-grove-making-it-last")],
    },
    {
        "id": "gerstner", "company": "IBM", "year": "1993", "role": "CEO", "tone": "exemplary",
        "title": "No vision, right now",
        "summary": "Lou Gerstner arrived at a struggling IBM, said 'the last thing IBM needs right now is a vision', and refused the planned break-up.",
        "story": [
            "When Lou Gerstner became IBM's CEO in 1993, the company was losing heavily and his predecessor had been preparing to split it into separate businesses. Many assumed Gerstner had been hired to finish the job.",
            "At a press conference after his first months he said the last thing IBM needed right now was a vision: it needed tough, market-driven strategies for each business. The press quoted the line without 'right now', which he later said was the important part.",
            "He kept IBM together, reasoning that customers wanted integrated solutions rather than fragmented technology, and later called it the most important decision he ever made.",
        ],
        "lesson": "In a turnaround, fix the basics and listen to customers before you write the grand statement. Don't take the obvious plan just because it was already prepared.",
        "sources": [("Lou Gerstner (Wikipedia)", "https://en.wikipedia.org/wiki/Lou_Gerstner")],
    },
    {
        "id": "kodak", "company": "Kodak", "year": "1975", "role": "CEO / CTO", "tone": "cautionary",
        "title": "The camera that was too good",
        "summary": "A Kodak engineer built the first self-contained digital camera. Management's reaction, he recalled: 'that's cute, but don't tell anyone about it.'",
        "story": [
            "In 1975 Steve Sasson, a young Kodak engineer, built the first self-contained digital camera. As he recalled it, management saw filmless photography as a threat to the hugely profitable film business.",
            "Kodak kept investing in digital research and even sold professional digital cameras in the 1990s, but it never moved its business model fast enough. It filed for bankruptcy protection in 2012.",
        ],
        "lesson": "If you don't cannibalise your own business, someone else will. Measure new technology by where it is heading, not by how it compares with your cash cow today.",
        "sources": [("BGR: The invention of digital cameras was almost buried at Kodak", "https://www.bgr.com/2246470/kodak-invention-digital-camera-explained/")],
    },
    {
        "id": "blockbuster", "company": "Blockbuster", "year": "2000", "role": "CEO", "tone": "cautionary",
        "title": "Passing on Netflix",
        "summary": "Netflix's founders offered to sell their company to Blockbuster for about $50 million. Blockbuster said no.",
        "story": [
            "Around 2000 Reed Hastings and his co-founder pitched Blockbuster on buying Netflix for about $50 million and running Blockbuster's online business. Blockbuster's leadership declined; Netflix looked like a small, loss-making niche.",
            "Late fees were a large source of Blockbuster's profit, and the customer resentment they created was part of Netflix's appeal. Blockbuster did later drop late fees and launch an online service, but years late. It went bankrupt in 2010.",
        ],
        "lesson": "Revenue your customers hate is a weakness, not a strength. A small, odd competitor that customers love deserves a serious look.",
        "sources": [("NBC: Netflix didn't kill Blockbuster", "https://www.nbcsandiego.com/news/business/money-report/netflix-didnt-kill-blockbuster-how-netflix-almost-lost-the-movie-rental-wars/2493680/")],
    },
    {
        "id": "qwikster", "company": "Netflix", "year": "2011", "role": "CEO / CMO", "tone": "cautionary",
        "title": "Qwikster",
        "summary": "A steep price rise, then an apology that announced a confusing split of the company. Netflix lost hundreds of thousands of subscribers in a quarter.",
        "story": [
            "In July 2011 Netflix separated its DVD and streaming plans, a price rise of up to 60% for people who wanted both. Customers were furious.",
            "In September, Reed Hastings apologised for how the change was communicated, and in the same message announced that the DVD business would become a separate service called Qwikster, with its own website. The apology was drowned out by a second shock. About three weeks later Netflix dropped Qwikster but kept the prices.",
            "Netflix lost about 800,000 US subscribers that quarter and its share price fell sharply. It recovered, and Hastings later called the episode a lesson in moving too fast without bringing customers along.",
        ],
        "lesson": "An apology must stand alone. Don't stack a second change on top of one customers are already angry about, and explain changes in terms of what customers get.",
        "sources": [("TIME: Netflix loses 800,000 subscribers after price hike, Qwikster debacle", "https://techland.time.com/2011/10/24/netflix-loses-800000-subscribers-after-price-hike-qwikster-debacle/"),
                    ("Yale SOM case: Netflix and Qwikster", "https://cases.som.yale.edu/netflix-and-qwikster")],
    },
    {
        "id": "starbucks2008", "company": "Starbucks", "year": "2008", "role": "CEO / COO", "tone": "exemplary",
        "title": "Closing 7,100 stores to make better coffee",
        "summary": "Howard Schultz returned as CEO and shut nearly every US store for an evening of espresso training.",
        "story": [
            "Howard Schultz came back as Starbucks CEO in January 2008 after a weak year in which, he felt, rapid growth had diluted the experience.",
            "On 26 February 2008, Starbucks closed about 7,100 US stores for roughly three hours so baristas could relearn how to pull espresso shots and steam milk. It cost the company several million dollars in lost sales, and rivals ran promotions that evening.",
            "The closure sent a message no memo could: quality of the core product came before short-term sales.",
        ],
        "lesson": "Symbolic actions that cost something are believed. If quality is the problem, fix it where the customer meets the product.",
        "sources": [("NPR: Starbucks baristas relearn art of coffee making (2008)", "https://www.npr.org/2008/02/27/54932288/starbucks-baristas-relearn-art-of-coffee-making")],
    },
    {
        "id": "nadella", "company": "Microsoft", "year": "2014", "role": "CEO / CHRO", "tone": "exemplary",
        "title": "From know-it-alls to learn-it-alls",
        "summary": "Satya Nadella made culture change, built on Carol Dweck's growth mindset, the centre of Microsoft's renewal.",
        "story": [
            "When Satya Nadella became CEO in 2014, Microsoft was known for internal rivalry and a culture he described as 'know-it-all'. He set out to make it 'learn-it-all', borrowing Carol Dweck's research on growth mindset.",
            "The change was built into how the company works: leaders defined what growth mindset meant in practice, it was repeated at meetings and built into evaluations, and an appraisal system that pitted employees against each other was replaced by one that asks how people helped others succeed.",
            "Microsoft's performance improved strongly in the following years. Culture was one factor among several, cloud strategy being another, but Nadella consistently named it as the foundation.",
        ],
        "lesson": "Culture changes when leaders change what is measured, rewarded and modelled, not when they publish values.",
        "sources": [("London Business School case: Satya Nadella at Microsoft", "https://www.london.edu/faculty-and-research/academic-research/s/satya-nadella-at-microsoft-instilling-a-growth-mindset"),
                    ("Fortune (2024): Nadella on learn-it-alls", "https://fortune.com/2024/05/20/satya-nadella-microsoft-culture-growth-mindset-learn-it-alls-know-it-alls/")],
    },
    {
        "id": "polman", "company": "Unilever", "year": "2009", "role": "CEO / CFO", "tone": "mixed",
        "title": "Ending quarterly guidance",
        "summary": "On becoming CEO, Paul Polman stopped giving quarterly earnings guidance to attract long-term investors.",
        "story": [
            "Paul Polman became Unilever's CEO in 2009 and, very early in his tenure, stopped giving quarterly earnings guidance. He argued that quarterly targets pushed managers into decisions that hurt long-term performance.",
            "The share price dropped when the change was announced. Polman said that not giving guidance attracted the right shareholders: those who would back a longer-term strategy. Unilever gave annual and long-term targets instead.",
        ],
        "lesson": "You choose your shareholders as much as they choose you. Communication with investors shapes the time horizon your managers work to.",
        "sources": [("Paul Polman (Wikipedia)", "https://en.wikipedia.org/wiki/Paul_Polman")],
    },
    {
        "id": "wellsfargo", "company": "Wells Fargo", "year": "2016", "role": "CEO / CHRO / Board", "tone": "cautionary",
        "title": "Two million accounts nobody asked for",
        "summary": "Aggressive cross-selling targets led employees to open accounts customers never requested. The CEO said there was no incentive to do bad things.",
        "story": [
            "In 2016 regulators fined Wells Fargo $185 million after finding that employees had opened roughly two million deposit and credit-card accounts without customers' permission. The bank had pushed staff hard to sell several products to every customer, with daily targets tracked closely.",
            "Thousands of junior employees had been fired over the years for the practice, while the targets stayed. CEO John Stumpf told Congress there was no incentive to do bad things; a later board report blamed the sales culture and the bank's decentralised structure.",
            "Stumpf resigned. The board clawed back about $75 million from him and the former head of community banking, and regulators later banned him from banking. His successor admitted the sales goals should have been removed sooner.",
        ],
        "lesson": "Incentives are the real values statement. When many people break a rule in the same way, look at the system before you blame the individuals.",
        "sources": [("Wells Fargo cross-selling scandal (Wikipedia)", "https://en.wikipedia.org/wiki/Wells_Fargo_cross-selling_scandal"),
                    ("SHRM: Wells Fargo to claw back $75 million", "https://shrm.org/topics-tools/news/benefits-compensation/wells-fargo-to-claw-back-75-million-incentive-pay-scandal")],
    },
    {
        "id": "boeingmax", "company": "Boeing", "year": "2019", "role": "CEO / Board / CFO", "tone": "cautionary",
        "title": "The 737 MAX",
        "summary": "Two crashes, 346 deaths, and a long debate about whether finance had come to outrank engineering.",
        "story": [
            "Two Boeing 737 MAX airliners crashed, in October 2018 and March 2019, killing 346 people, and the fleet was grounded worldwide. Investigations pointed to a flight-control system and to how it had been designed, certified and explained to pilots.",
            "Critics argued that, since the 1997 McDonnell Douglas merger, Boeing's culture had shifted from engineering towards cost and schedule pressure and shareholder returns. Reporting noted that the board approved a $20 billion share buyback less than two months after the first crash, later shelved.",
            "Business schools now teach the case as a question: how should leaders who are not engineers oversee safety-critical engineering?",
        ],
        "lesson": "When safety and quality are the product, the board and the C-suite need direct, unfiltered lines to the engineers, and financial targets must never quietly outrank them.",
        "sources": [("Stanford GSB case: Boeing 737 MAX", "https://www.gsb.stanford.edu/faculty-research/publications/boeing-737-max"),
                    ("Fortune: The 737 MAX crisis and Boeing's shareholder-first culture", "https://fortune.com/longform/boeing-737-max-crisis-shareholder-first-culture")],
    },
    {
        "id": "gmignition", "company": "General Motors", "year": "2014", "role": "CEO", "tone": "exemplary",
        "title": "Owning a decade-old failure",
        "summary": "Weeks into her tenure, Mary Barra faced a deadly ignition-switch defect that GM had failed to recall for years. She commissioned a brutally honest report and published its findings.",
        "story": [
            "Mary Barra became CEO of GM in January 2014. Within weeks the company recalled cars with a faulty ignition switch that could cut power while driving, linked to deaths, a defect some at GM had known about for years.",
            "Barra commissioned former US Attorney Anton Valukas to investigate. She called his report 'brutally tough and deeply troubling', described a pattern of incompetence and neglect, removed 15 employees, and set up a compensation programme for victims run by Kenneth Feinberg. She also went to Congress and answered the questions herself.",
        ],
        "lesson": "Inheriting a problem doesn't make it someone else's. Commission the truth, publish it, fix the system and compensate the people harmed.",
        "sources": [("PBS NewsHour: internal report on GM's delayed recall", "https://www.pbs.org/newshour/show/internal-report-doesnt-answer-gm-didnt-address-safety-issue-earlier")],
    },
    {
        "id": "bphayward", "company": "BP", "year": "2010", "role": "CEO", "tone": "cautionary",
        "title": "“I'd like my life back”",
        "summary": "Weeks into the Deepwater Horizon spill, which killed 11 workers, BP's CEO told reporters he would like his life back.",
        "story": [
            "The Deepwater Horizon rig exploded in April 2010, killing 11 people and starting the largest marine oil spill in US history. BP's CEO, Tony Hayward, became the company's face in the Gulf.",
            "In May, after apologising to residents, he added that nobody wanted the spill over more than he did and that he would like his life back. The remark put the CEO's discomfort next to the families of the dead. Later photographs of him at a yacht race made it worse. He stepped down that year.",
        ],
        "lesson": "In a crisis, every word is about the people harmed, never about you. Prepare the spokesperson, and stop when the message is delivered.",
        "sources": [("NPR: BP, a textbook example of how not to handle PR (2011)", "https://www.kunc.org/npr-news/2011-04-21/bp-a-textbook-example-of-how-not-to-handle-pr")],
    },
    {
        "id": "maersk", "company": "A.P. Moller-Maersk", "year": "2017", "role": "CIO / CEO / Board", "tone": "mixed",
        "title": "NotPetya and the server in Ghana",
        "summary": "A cyberweapon wiped Maersk's IT in hours. One domain controller in Ghana, offline because of a power cut, made recovery possible.",
        "story": [
            "In June 2017 the NotPetya malware spread through Maersk's network and destroyed its systems worldwide. The world's largest container shipping company ran on manual processes for about ten days.",
            "Recovery hinged on luck: a domain controller in Accra, Ghana, had been offline during a power outage and held a clean copy of the company's directory. Staff flew it to the UK. Maersk rebuilt thousands of servers and tens of thousands of PCs, and estimated the cost at $250 to $300 million.",
            "Chairman Jim Hagemann Snabe spoke openly about it at Davos, saying Maersk had been 'basically average' at cybersecurity, a rare public admission that helped others learn.",
        ],
        "lesson": "Plan for recovery, not just prevention. Offline backups and rehearsed rebuilds decide how long a cyber crisis lasts.",
        "sources": [("SC Magazine: NotPetya attack totally destroyed Maersk's network", "https://scmagazine.com/news/notpetya-attack-totally-destroyed-maersks-computer-network-chairman"),
                    ("Redmond: the domain controller nightmare", "https://redmondmag.com/blogs/scott-bekker/2018/08/domain-controller-nightmare.aspx")],
    },
    {
        "id": "equifax", "company": "Equifax", "year": "2017", "role": "CIO / CISO / CEO", "tone": "cautionary",
        "title": "The patch that wasn't applied",
        "summary": "A known web-software flaw, with a fix available for two months, exposed the personal data of about 147 million people.",
        "story": [
            "In March 2017 a serious vulnerability in Apache Struts was published along with a fix. Equifax's scans failed to find the vulnerable system and it was never patched. Attackers got in and stayed for weeks.",
            "Reporting and a later Senate report described slow internal escalation, policies that existed on paper but weren't followed, and weak board oversight of cyber risk. The CEO, CIO and chief security officer left.",
        ],
        "lesson": "Security is a management system, not a tool. Know your assets, make patching measurable, and make sure bad news reaches the top in hours, not weeks.",
        "sources": [("Help Net Security: Equifax breach happened because of a missed patch", "https://www.helpnetsecurity.com/2017/09/14/equifax-breach-patch/"),
                    ("Computer Weekly: Equifax and the Senate report", "https://www.computerweekly.com/news/252459085/Equifax-defends-against-scathing-Senate-report")],
    },
    {
        "id": "crowdstrike", "company": "CrowdStrike", "year": "2024", "role": "CEO / CTO", "tone": "mixed",
        "title": "One update, 8.5 million screens",
        "summary": "A faulty content update crashed millions of Windows machines worldwide. The first statement explained, but didn't apologise.",
        "story": [
            "On 19 July 2024 a faulty content update from CrowdStrike crashed about 8.5 million Windows computers, grounding flights and disrupting hospitals and banks around the world. Fixing many machines meant touching them one by one.",
            "CEO George Kurtz's first public statement explained that it was not a cyberattack, but did not apologise; he apologised hours later after a public backlash. The company then published reviews and changed how it rolls out updates, including staged deployment.",
        ],
        "lesson": "Lead with empathy and ownership, then the technical facts. And treat anything that ships to every customer at once as a one-way door.",
        "sources": [("Fortune: CEO at the firm that caused a global outage forgot to apologize", "https://fortune.com/2024/07/19/ceo-at-cybersecurity-firm-that-caused-a-global-outage-forgot-to-apologize")],
    },
    {
        "id": "southwest", "company": "Southwest Airlines", "year": "2022", "role": "COO / CIO", "tone": "cautionary",
        "title": "The Christmas meltdown",
        "summary": "A winter storm overwhelmed Southwest's crew-scheduling software, and the airline cancelled about 16,700 flights in ten days.",
        "story": [
            "In late December 2022 a winter storm disrupted flights across the US. Most airlines recovered in days. Southwest's crew-scheduling tools could not keep up with the reassignments, so schedulers fell back to phone calls and manual work while crews and planes were stranded in the wrong places.",
            "Unions had warned for years that the scheduling technology was outdated; the pilots' union had predicted a meltdown weeks before. The disruption cost the airline hundreds of millions and a great deal of goodwill.",
        ],
        "lesson": "Technical debt is a business risk that compounds silently. Listen when front-line people warn that the system breaks under stress.",
        "sources": [("Dallas Morning News: what's the problem with Southwest's scheduling system", "https://dallasnews.com/business/airlines/2022/12/30/whats-the-problem-with-southwest-airlines-scheduling-system"),
                    ("2022 Southwest Airlines scheduling crisis (Wikipedia)", "https://en.wikipedia.org/wiki/2022_Southwest_Airlines_scheduling_crisis")],
    },
    {
        "id": "svb", "company": "Silicon Valley Bank", "year": "2023", "role": "CFO / CRO / Board", "tone": "cautionary",
        "title": "The bank that bought long bonds",
        "summary": "SVB put a flood of deposits into long-dated bonds. When rates rose, losses mounted, depositors ran, and the bank failed in two days.",
        "story": [
            "During the boom of 2020 and 2021, Silicon Valley Bank's deposits ballooned and it invested much of them in long-dated government and mortgage bonds. By the end of 2022 it held about $91 billion in 'held-to-maturity' securities with unrealised losses of more than $15 billion, and very little interest-rate hedging.",
            "Its depositors were concentrated in tech and venture capital, and most deposits were above the insured limit. When the bank announced a loss on bond sales and a capital raise in March 2023, depositors withdrew money at unprecedented speed. Regulators closed it two days later.",
            "Reporting also noted that the bank had been without a permanent chief risk officer for much of 2022, while rates were rising.",
        ],
        "lesson": "Match the duration of what you own to the stability of what you owe, stress-test for the scenario everyone thinks is unlikely, and never leave the risk seat empty in a storm.",
        "sources": [("Collapse of Silicon Valley Bank (Wikipedia)", "https://en.wikipedia.org/wiki/Collapse_of_Silicon_Valley_Bank"),
                    ("GARP: SVB, a failure in risk management", "https://www.garp.org/white-paper/silicon-valley-bank-a-failure-in-risk-management")],
    },
    {
        "id": "theranos", "company": "Theranos", "year": "2015", "role": "Board / CEO", "tone": "cautionary",
        "title": "A famous board that couldn't see",
        "summary": "Theranos had a board of statesmen and generals, and almost no one on it who understood blood testing.",
        "story": [
            "Theranos claimed it could run many blood tests on a few drops of blood. It raised hundreds of millions and assembled a board of former cabinet secretaries, senators and military leaders.",
            "Very few board members had scientific or medical expertise, and the board relied on reassurance and outside credibility rather than independent testing. Reporting in 2015 exposed that the technology did not work as claimed. The company collapsed, and its founder was later convicted of fraud.",
        ],
        "lesson": "A board's prestige is no substitute for relevant expertise and independent verification. Directors must be able to test what they're told.",
        "sources": [("Governance Intelligence: what Theranos can teach start-ups about governance", "https://governance-intelligence.com/boardroom/what-theranos-calamity-can-teach-start-ups-about-governance")],
    },
    {
        "id": "disney", "company": "The Walt Disney Company", "year": "2022", "role": "Board / CEO / CHRO", "tone": "cautionary",
        "title": "The succession that unravelled",
        "summary": "Bob Iger's hand-picked successor lasted under three years before the board brought Iger back.",
        "story": [
            "Bob Chapek succeeded Bob Iger as Disney's CEO in 2020, while Iger stayed on as executive chairman. The arrangement split authority, and reporting described former Iger lieutenants and directors questioning Chapek's decisions.",
            "In November 2022 the board removed Chapek and brought Iger back. Commentators blamed the board for deferring to the former CEO and for an unclear process. The board then created a dedicated succession committee.",
        ],
        "lesson": "Succession is the board's job, not the outgoing CEO's. Start years ahead, keep a real bench, and give the new leader clear authority.",
        "sources": [("Axios: Disney just revealed how not to do a CEO succession plan", "https://www.axios.com/2022/11/22/disney-ceo-succession-iger-chapek-board"),
                    ("Fortune: boomerang CEOs and succession planning", "https://fortune.com/2023/04/17/boomerang-ceo-bob-iger-disney-ubs-starbucks-howard-schultz-succession-planning/")],
    },
    {
        "id": "patagonia", "company": "Patagonia", "year": "2011 / 2022", "role": "CMO / CEO", "tone": "exemplary",
        "title": "Don't buy this jacket",
        "summary": "A Black Friday ad told customers not to buy a best-selling jacket. Eleven years later the founders gave the company away to fight climate change.",
        "story": [
            "On Black Friday 2011, Patagonia ran a full-page New York Times ad showing one of its own fleece jackets under the headline 'Don't Buy This Jacket', listing the environmental cost of making it and asking people to buy only what they need and repair what they own.",
            "In 2022 founder Yvon Chouinard and his family transferred ownership: the voting shares to a purpose trust and the rest to a non-profit that uses the company's profits to fight climate change.",
            "Critics have noted that the transfer also avoided a large tax bill. Supporters point out that the brand's promise and its behaviour have stayed consistent for decades.",
        ],
        "lesson": "A brand is a promise kept over time. Marketing that matches what the company actually does builds trust that competitors can't copy.",
        "sources": [("University of Manchester: six months on from Patagonia's restructuring", "https://sites.manchester.ac.uk/political-perspectives/2023/04/17/profit-for-the-planet-six-months-on-from-patagonias-radical-restructuring/")],
    },
    {
        "id": "nooyi", "company": "PepsiCo", "year": "2006 to 2018", "role": "CEO / CHRO", "tone": "exemplary",
        "title": "Letters to the parents",
        "summary": "Indra Nooyi wrote to the parents of her senior executives to thank them for 'the gift of your child' to the company.",
        "story": [
            "After a visit home to India, where relatives and neighbours congratulated her mother on her success, PepsiCo CEO Indra Nooyi realised her executives' parents rarely saw that kind of recognition.",
            "She began writing personal letters to the parents of her senior team, describing what their son or daughter was doing at PepsiCo. Over time she wrote hundreds, and later wrote to spouses too. She said it changed the morale and loyalty of her team.",
        ],
        "lesson": "Recognition that is personal, specific and unexpected is cheap to give and lasts for years.",
        "sources": [("Fortune: the CEO who writes her employees' parents (2014)", "https://fortune.com/2014/01/28/say-wha-the-ceo-who-writes-her-employees-parents/")],
    },
    {
        "id": "teledyne", "company": "Teledyne", "year": "1972 to 1984", "role": "CEO / CFO", "tone": "exemplary",
        "title": "The buyback master",
        "summary": "Henry Singleton issued stock when it was expensive and bought it back when it was cheap, repurchasing most of Teledyne's shares.",
        "story": [
            "In the 1960s Henry Singleton used Teledyne's highly valued shares to buy dozens of companies. When the market turned and the shares became cheap in the 1970s and early 1980s, he reversed course and bought back a very large share of the company's stock, often through tender offers.",
            "In William Thorndike's book The Outsiders, Singleton is the model of a CEO whose main job is capital allocation: putting every dollar where it earns the most per share, ignoring fashion and size for its own sake.",
        ],
        "lesson": "A CEO's most underrated job is deciding where the money goes. Judge every option, including buying back your own shares, by long-term value per share.",
        "sources": [("Farnam Street: Henry Singleton, distant force", "https://fs.blog/knowledge-project-podcast/outliers-henry-singleton/")],
    },
]

CASE_BY_ID = {c["id"]: c for c in CASES}
