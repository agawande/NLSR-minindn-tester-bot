Usage: sudo python testnlsr.py exp_file work_dir

sudo python testnlsr.py --help

Without stopping testnlsr:
(1) exp_file can be update anytime to add new experiments
(2) minindn can be updated anytime
(3) work_dir/record.json can be updated if something goes wrong to retest a patch


Mini-NDN is modified to make it work on arcturus:
(1) Uses nfd.conf.sample by default instead of nfd.conf
(2) Changes to ndn_app to correctly get PID
(3) Sleep after NLSR to avoid default certificate error
(4) New experiments:
    (4.1) Convergence - does nothing, exits after convergence
    (4.2) MCN failure convergence - same as MCN failure but no pings and checks convergence after node comes back up
