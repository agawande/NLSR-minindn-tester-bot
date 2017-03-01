Usage: sudo python testnlsr.py exp_file work_dir

sudo python testnlsr.py --help

The bot is dependent on:
(1) PyGerrit2
(2) Mini-NDN

Without stopping testnlsr:
(1) exp_file can be update anytime to add new experiments
(2) minindn can be updated anytime
(3) To retrigger a patch simply change the verified-integration score to zero on your patch

This bot also tests Mini-NDN patches so as to provide up-to-date integration testing:
(1) For Mini-NDN testing it simply tests all the experiments of Mini-NDN on the default topology.
(2) For Mini-NDN patches the bot will use the verified label

If conf file updated, both Mini-NDN and NLSR changes may fail and then can be updated one by one.
