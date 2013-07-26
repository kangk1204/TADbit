"""
16 Dec 2012


"""
from bisect   import bisect_left
from numpy    import std
from math     import log10
from re       import sub
from warnings import warn
import numpy as np
from subprocess import Popen, PIPE

try:
    from matplotlib import pyplot as plt
except ImportError:
    warn('matplotlib not found\n')


def get_r2 (fun, X, Y, *args):
    sstot = sum([(Y[i]-np.mean(Y))**2 for i in xrange(len(Y))])
    sserr = sum([(Y[i] - fun(X[i], *args))**2 for i in xrange(len(Y))])
    return 1 - sserr/sstot


def filter_by_zero_count(matrx, draw_hist=False):
    """
    fits the distribution of Hi-C interaction count by column in the matrix to
    a polynomial. Then searches for the first possible 
    """
    nbins = 100
    # get sum of columns
    cols = []
    for c in sorted(matrx, key=sum):
        cols.append(len(c) - c.count(0))
    cols = np.array(cols)
    if draw_hist:
        plt.figure(figsize=(9, 9))
    median = np.median(cols)
    # mad = np.median([abs(median - c ) for c in cols])
    best =(None, None, None, None)
    # bin the sum of columns
    xmin = min(cols)
    xmax = max(cols)
    y = np.linspace(xmin, xmax, nbins)
    hist = np.digitize(cols, y)
    x = [sum(hist == i) for i in range(1, nbins + 1)]
    if draw_hist:
        hist = plt.hist(cols, bins=100, alpha=.3, color='grey')
    xp = range(0, cols[-1])
    # check if the binning is correct
    # we want at list half of the bins with some data
    while list(x).count(0) > 2*len(x)/3:
        cols = cols[:-1]
        xmin = min(cols)
        xmax = max(cols)
        y = np.linspace(xmin, xmax, nbins)
        hist = np.digitize(cols, y)
        x = [sum(hist == i) for i in range(1, nbins + 1)]
        if draw_hist:
            plt.clf()
            hist = plt.hist(cols, bins=100, alpha=.3, color='grey')
        xp = range(0, cols[-1])
    # find best polynomial fit in a given range
    for order in range(7, 14):
        z = np.polyfit(y, x, order)
        zpp = np.polyder(z, m=1)
        roots = np.roots(np.polyder(z))
        # check that we are concave down, otherwise take next root
        pente = np.polyval(zpp, abs(roots[-2] - roots[-1]) / 2 + roots[-1])
        if pente > 0:
            root = roots[-1]
        else:
            root = roots[-2]
        # root must be higher than zero
        if root <= 0:
            continue
        # and lower than the median
        if root >= median:
            continue
        p  = np.poly1d(z)
        R2 = get_r2(p, x, y)
        if best[0] < R2:
            best = (R2, order, p, z, root)
    p, z, root = best[2:]
    if draw_hist:
        a = plt.plot(xp, p(xp), "--", color='k')
        b = plt.vlines(root, 0, plt.ylim()[1], colors='r', linestyles='dashed')
        plt.legend(a+[b], ['polyfit \n{}'.format(
            ''.join([sub('e([-+][0-9]+)', 'e^{\\1}',
                         '${}{:.1}x^{}$'.format('+' if j>0 else '', j,
                                                '{' + str(i) + '}'))
                     for i, j in enumerate(list(p)[::-1])])),
                               'first solution of polynomial derivation'],
                   fontsize='x-small')
        plt.ylim(0, plt.ylim()[1])
        plt.show()
    # label as bad the columns with sums lower than the root
    bads = []
    for i, col in enumerate(matrx):
        if sum(col) < root:
            bads.append(i)
    # now stored in Experiment._zeros, used for getting more accurate z-scores
    return bads


def filter_by_mean(matrx, draw_hist=False):
    """
    fits the distribution of Hi-C interaction count by column in the matrix to
    a polynomial. Then searches for the first possible 
    """
    nbins = 100
    # get sum of columns
    cols = []
    for c in sorted(matrx, key=sum):
        cols.append(sum(c))
    cols = np.array(cols)
    if draw_hist:
        plt.figure(figsize=(9, 9))
    median = np.median(cols)
    # mad = np.median([abs(median - c ) for c in cols])
    best =(None, None, None, None)
    # bin the sum of columns
    xmin = min(cols)
    xmax = max(cols)
    y = np.linspace(xmin, xmax, nbins)
    hist = np.digitize(cols, y)
    x = [sum(hist == i) for i in range(1, nbins + 1)]
    if draw_hist:
        hist = plt.hist(cols, bins=100, alpha=.3, color='grey')
    xp = range(0, cols[-1])
    # check if the binning is correct
    # we want at list half of the bins with some data
    while list(x).count(0) > len(x)/2:
        cols = cols[:-1]
        xmin = min(cols)
        xmax = max(cols)
        y = np.linspace(xmin, xmax, nbins)
        hist = np.digitize(cols, y)
        x = [sum(hist == i) for i in range(1, nbins + 1)]
        if draw_hist:
            plt.clf()
            hist = plt.hist(cols, bins=100, alpha=.3, color='grey')
        xp = range(0, cols[-1])
    # find best polynomial fit in a given range
    for order in range(4, 14):
        z = np.polyfit(y, x, order)
        zp = np.polyder(z, m=1)
        roots = np.roots(np.polyder(z))
        # check that we are concave down, otherwise take next root
        pente = np.polyval(zp, abs(roots[-2] - roots[-1]) / 2 + roots[-1])
        if pente > 0:
            root = roots[-1]
        else:
            root = roots[-2]
        # root must be higher than zero
        if root <= 0:
            continue
        # and lower than the median
        if root >= median:
            continue
        p  = np.poly1d(z)
        R2 = get_r2(p, x, y)
        if best[0] < R2:
            best = (R2, order, p, z, root)
    p, z, root = best[2:]
    if draw_hist:
        a = plt.plot(xp, p(xp), "--", color='k')
        b = plt.vlines(root, 0, plt.ylim()[1], colors='r', linestyles='dashed')
        # c = plt.vlines(median - mad * 1.5, 0, 110, colors='g',
        #                linestyles='dashed')
        plt.legend(a+[b], ['polyfit \n{}'.format(
            ''.join([sub('e([-+][0-9]+)', 'e^{\\1}',
                         '${}{:.1}x^{}$'.format('+' if j>0 else '', j,
                                                '{' + str(i) + '}'))
                     for i, j in enumerate(list(p)[::-1])])),
                               'first solution of polynomial derivation'],
                   fontsize='x-small')
        # plt.legend(a+[b]+[c], ['polyfit \n{}'.format(
        #     ''.join([sub('e([-+][0-9]+)', 'e^{\\1}',
        #                  '${}{:.1}x^{}$'.format('+' if j>0 else '', j,
        #                                         '{' + str(i) + '}'))
        #              for i, j in enumerate(list(p)[::-1])])),
        #                        'first solution of polynomial derivation',
        #                        'median - (1.5 * median absolute deviation)'],
        #            fontsize='x-small')
        plt.ylim(0, plt.ylim()[1])
        plt.show()
    # label as bad the columns with sums lower than the root
    bads = []
    for i, col in enumerate(matrx):
        if sum(col) < root:
            bads.append(i)
    # now stored in Experiment._zeros, used for getting more accurate z-scores
    return bads


def filter_by_stdev(matrx):
    means = [np.mean(c) for c in matrx]
    mean = np.mean(means)
    stde = np.std(means)
    root = mean - stde * 1.25
    # label as bad the columns with sums lower than the root
    bads = []
    for i, col in enumerate(matrx):
        if sum(col) < root:
            bads.append(i)
    # now stored in Experiment._zeros, used for getting more accurate z-scores
    return bads


def filter_by_mad(matrx):
    # get sum of columns
    cols = []
    for c in sorted(matrx, key=sum):
        cols.append(sum(c))
    cols = np.array(cols)
    median = np.median(cols)
    mad = np.median([abs(median - c ) for c in cols])
    root = median - mad * 1.5
    # label as bad the columns with sums lower than the root
    bads = []
    for i, col in enumerate(matrx):
        if sum(col) < root:
            bads.append(i)
    # now stored in Experiment._zeros, used for getting more accurate z-scores
    return bads


def hic_filtering_for_modelling(matrx, method='mean'):
    """
    :param matrx: Hi-C matrix of a given experiment
    :param mean method: method to use for filtering Hi-C columns. Aims to
       remove columns with abnormally low count of interactions

    :returns: the indexes of the columns not to be considered for the
       calculation of the z-score
    """
    if method == 'mean':
        bads = filter_by_mean(matrx, draw_hist=False)
    elif method == 'zeros':
        bads = filter_by_zero_count(matrx)
    elif method == 'mad':
        bads = filter_by_mad(matrx)
    elif method == 'stdev':
        bads = filter_by_stdev(matrx)
    else:
        raise Exception
    return bads


class Interpolate(object):
    """
    simple linear interpolation
    """
    def __init__(self, x_list, y_list):
        for i, (x, y) in enumerate(zip(x_list, x_list[1:])):
            if y - x < 0:
                raise ValueError("x must be in strictly ascending")
            if y - x == 0 and i >= len(x_list)-2:
                x_list = x_list[:-1]
                y_list = y_list[:-1]
        if any(y - x <= 0 for x, y in zip(x_list, x_list[1:])):
            raise ValueError("x must be in strictly ascending")
        x_list = self.x_list = map(float, x_list)
        y_list = self.y_list = map(float, y_list)
        intervals = zip(x_list, x_list[1:], y_list, y_list[1:])
        self.slopes = [(y2 - y1)/(x2 - x1) for x1, x2, y1, y2 in intervals]
        
    def __call__(self, x):
        i = bisect_left(self.x_list, x) - 1
        return self.y_list[i] + self.slopes[i] * (x - self.x_list[i])


class matrix(object):
    """
    simple object to store hi-c matrices. Only keeps half matrix
    values MUST be integers
    matrices MUST be symetric
    """
    def __init__(self, nums, size):
        """
        
        """
        self.values = reduce_matrix(nums, size)
        self.nrows  = size


    def rebuild_matrix(self):
        values = [[[] for _ in xrange(self.nrows)] for _ in xrange(self.nrows)]
        for i in xrange(self.nrows):
            for j in xrange(self.nrows):
                values[i][j] = self.values[i*(j-i)]
        return values


def reduce_matrix(nums, size):
    return tuple([nums[i*j] for i in xrange(size) for j in xrange(i, size)])


def zscore(values, size):
    """
    _______________________/___
                          /
                         /
                        /
                       /
                      /
                     /
                    /
                   /
                  /
                 /
                /
               /
              /                     score
          ___/_________________________________
            /

    """
    # do not take into account the diagonal
    nop = dict([(i + size * i,  None) for i in xrange(size)])
    minv = min([v for v in values if v]) / 2
    # get the log10 of values
    vals = [log10(v) if v > 0 and not v in nop else log10(minv) for v in values]
    mean_v = np.mean(vals)
    std_v = std(vals)
    # replace values by z-score
    for i in xrange(len(values)):
        if values[i] > 0:
            values[i] = (vals[i] - mean_v) / std_v
        elif values[i] == 0:
            values[i] = (log10(minv) - mean_v) / std_v
        else:
            values[i] = -99


def nicer(res):
    """
    writes resolution number for human beings.
    """
    if not res % 1000000000:
        return str(res)[:-9] + 'Gb'
    if not res % 1000000:
        return str(res)[:-6] + 'Mb'
    if not res % 1000:
        return str(res)[:-3] + 'Kb'
    return str(res) + 'b'


COLOR = {None: '\033[31m', # red
         0   : '\033[34m', # blue
         1   : '\033[34m', # blue
         2   : '\033[34m', # blue
         3   : '\033[36m', # cyan
         4   : '\033[0m' , # white
         5   : '\033[1m' , # bold white
         6   : '\033[33m', # yellow
         7   : '\033[33m', # yellow
         8   : '\033[35m', # purple
         9   : '\033[35m', # purple
         10  : '\033[31m'  # red
         }

COLORHTML = {None: '<span style="color:red;">'       , # red
             0   : '<span>'                          , # blue
             1   : '<span style="color:blue;">'      , # blue
             2   : '<span style="color:blue;">'      , # blue
             3   : '<span style="color:purple;">'    , # purple
             4   : '<span style="color:purple;">'    , # purple
             5   : '<span style="color:teal;">'      , # cyan
             6   : '<span style="color:teal;">'      , # cyan
             7   : '<span style="color:olive;">'     , # yellow
             8   : '<span style="color:olive;">'     , # yellow
             9   : '<span style="color:red;">'       , # red
             10  : '<span style="color:red;">'         # red
             }


def colorize(string, num, ftype='ansi'):
    """
    Colorize with ANSII colors a string for printing in shell. this acording to
    a given number between 0 and 10

    :param string: the string to colorize
    :param num: a number between 0 and 10 (if None, number will be equal to 10)

    :returns: the string 'decorated' with ANSII color code
    """
    color = COLOR if ftype=='ansi' else COLORHTML
    return '{}{}{}'.format(color[num], string,
                           '\033[m' if ftype=='ansi' else '</span>')


def color_residues(n_part):
    """
    :param n_part: number of particles
    
    :returns: a list of rgb tuples (red, green, blue)
    """
    result = []
    for n in xrange(n_part):
        red = float(n + 1) / n_part
        result.append((red, 1 - red, 0))
    return result


def calc_eqv_rmsd(models, nloci, dcutoff=200, fact=0.75, var='score',
                  tmp_file='/tmp/tmp.xyz', tm_bin='eqv-drmsd-concat-xyz'):
    """
    :param score var: value to return.
    
    :returns: a score (depends on 'var' argument)
    """
    out = ''
    form = "{:>12}{:>12}{:>12.3f}{:>12.3f}{:>12.3f}\n"
    for model in models:
        out += 'model_{}\n'.format(model)
        for n in xrange(nloci):
            out += form.format('p' + str(n + 1), n + 1,
                               models[model]['x'][n],
                               models[model]['y'][n],
                               models[model]['z'][n])
    out_f = open(tmp_file, 'w')
    out_f.write(out)
    out_f.close()
    out = Popen(tm_bin + ' ' + tmp_file + ' {} {}'.format(nloci, dcutoff),
                shell=True, stdout=PIPE).communicate()[0]
    drmsds, rmsds = zip(*[(float(line.split()[3]), float(line.split()[4]))
                          for line in out.split('\n') if line])
    max_drmsd = max(drmsds)
    max_rmsd  = max(rmsds)
    scores = []
    for line in out.split('\n'):
        if not line:
            continue
        m1, m2, eqv, drmsd, rmsd = line.split()
        if var=='score':
            score = float(eqv) * ((float(drmsd) / max_drmsd) / (float(rmsd) / max_rmsd))
        elif var=='drmsd':
            scores.append(drmsd)
            continue
        if score > fact * nloci:
            scores.append((m1, m2, score))
        else:
            scores.append((m1, m2, 0.0))
    return scores


def augmented_dendrogram(clust_count=None, dads=None, energy=None, color=False,
                         *args, **kwargs):

    from scipy.cluster.hierarchy import dendrogram
    fig = plt.figure()
    ddata = dendrogram(*args, **kwargs)
    plt.clf()
    ax = fig.add_subplot(1, 1, 1)   # left, bottom, width, height:
                                                # (adjust as necessary)
    ax.patch.set_facecolor('lightgrey')
    ax.patch.set_alpha(0.4)
    ax.grid(ls='-', color='w', lw=1.5, alpha=0.6, which='major')
    ax.grid(ls='-', color='w', lw=1, alpha=0.3, which='minor')
    ax.set_axisbelow(True)
    # remove tick marks
    ax.tick_params(axis='both', direction='out', top=False, right=False,
                   left=False, bottom=False)
    ax.tick_params(axis='both', direction='out', top=False, right=False,
                   left=False, bottom=False, which='minor')

    # set dict to store data of each cluster (count and energy), depending on
    # x position in graph.
    leaves = {}
    dist = ddata['icoord'][0][2] - ddata['icoord'][0][1]
    for i, x in enumerate(ddata['leaves']):
        leaves[dist*i + dist/2] = x
    minnrj = min(energy.values())-1
    maxnrj = max(energy.values())-1
    difnrj = maxnrj - minnrj
    total = sum(clust_count.values())
    if not kwargs.get('no_plot', False):
        for i, d, c in zip(ddata['icoord'], ddata['dcoord'],
                           ddata['color_list']):
            x = 0.5 * sum(i[1:3])
            y = d[1]
            # plt.plot(x, y, 'ro')
            plt.hlines(y, i[1], i[2], lw=2, color='grey')
            # for eaxch branch
            for i1, d1, d2 in zip(i[1:3], [d[0], d[3]], [d[1], d[2]]):
                try:
                    lw = float(clust_count[leaves[i1]])/total*10*len(leaves)
                except KeyError:
                    lw = 1.0
                nrj = energy[leaves[i1]] if leaves[i1] in energy else maxnrj
                plt.vlines(i1, d1-(difnrj-(nrj-minnrj)), d2, lw=lw,
                           color=(c if color else 'grey'))
                if leaves[i1] in energy:
                    plt.annotate("%.3g" % (leaves[i1]),
                                 (i1, d1-(difnrj-(nrj-minnrj))),
                                 xytext=(0, -8),
                                 textcoords='offset points',
                                 va='top', ha='center')
            leaves[(i[1] + i[2])/2] = dads[leaves[i[1]]]
    bot = -int(difnrj)/10000 * 10000
    plt.yticks([bot+i for i in xrange(0, -bot-bot/10, -bot/10)],
               ["{:,}".format(int(minnrj)/10000 * 10000  + i)
                for i in xrange(0, -bot-bot/10, -bot/10)], size='small')
    plt.ylabel('Minimum IMP objective function')
    plt.xticks([])
    plt.xlim((plt.xlim()[0] - 2, plt.xlim()[1]))
    fig.suptitle("Dendogram of clusters of 3D models")
    ax.set_title("Branch length proportional to model's energy\n" +
              "Branch width to the number of models in the cluster", size='small')
    plt.show()

    return ddata


def plot_hist_box(data, part1, part2):
    # setup the figure and axes
    fig = plt.figure()
    bpAx = fig.add_axes([0.2, 0.7, 0.7, 0.2])   # left, bottom, width, height:
                                                # (adjust as necessary)
    bpAx.patch.set_facecolor('lightgrey')
    bpAx.patch.set_alpha(0.4)
    bpAx.grid(ls='-', color='w', lw=1.5, alpha=0.6, which='major')
    bpAx.grid(ls='-', color='w', lw=1, alpha=0.3, which='minor')
    bpAx.set_axisbelow(True)
    bpAx.minorticks_on() # always on, not only for log
    # remove tick marks
    bpAx.tick_params(axis='both', direction='out', top=False, right=False,
                   left=False, bottom=False)
    bpAx.tick_params(axis='both', direction='out', top=False, right=False,
                   left=False, bottom=False, which='minor')
    # plot stuff
    bp = bpAx.boxplot(data, vert=False)
    plt.setp(bp['boxes'], color='black')
    plt.setp(bp['whiskers'], color='black')
    plt.setp(bp['medians'], color='darkred')
    plt.setp(bp['fliers'], color='darkred', marker='+')
    bpAx.plot(sum(data)/len(data), 1, 
              color='w', marker='*', markeredgecolor='k')
    bpAx.annotate('{:.4}'.format(bp['boxes'][0].get_xdata()[0]),
                  (bp['boxes'][0].get_xdata()[0], bp['boxes'][0].get_ydata()[1]),
                  va='bottom', ha='center', xytext=(0, 2),
                  textcoords='offset points',
                  size='small')
    bpAx.annotate('{:.4}'.format(bp['boxes'][0].get_xdata()[2]),
                  (bp['boxes'][0].get_xdata()[2], bp['boxes'][0].get_ydata()[1]),
                  va='bottom', ha='center', xytext=(0, 2),
                  textcoords='offset points',
                  size='small')
    bpAx.annotate('{:.4}'.format(bp['medians'][0].get_xdata()[0]),
                  (bp['medians'][0].get_xdata()[0], bp['boxes'][0].get_ydata()[0]),
                  va='top', ha='center', xytext=(0, -2),
                  textcoords='offset points', color='darkred',
                  size='small')
    histAx = fig.add_axes([0.2, 0.2, 0.7, 0.5]) # left specs should match and
                                                # bottom + height on this line should
                                                # equal bottom on bpAx line
    histAx.patch.set_facecolor('lightgrey')
    histAx.patch.set_alpha(0.4)
    histAx.grid(ls='-', color='w', lw=1.5, alpha=0.6, which='major')
    histAx.grid(ls='-', color='w', lw=1, alpha=0.3, which='minor')
    histAx.set_axisbelow(True)
    histAx.minorticks_on() # always on, not only for log
    # remove tick marks
    histAx.tick_params(axis='both', direction='out', top=False, right=False,
                   left=False, bottom=False)
    histAx.tick_params(axis='both', direction='out', top=False, right=False,
                   left=False, bottom=False, which='minor')
    h = histAx.hist(data, bins=20, alpha=0.5, color='darkgreen')
    # confirm that the axes line up 
    xlims = np.array([bpAx.get_xlim(), histAx.get_xlim()])
    for ax in [bpAx, histAx]:
        ax.set_xlim([xlims.min(), xlims.max()])
    bpAx.set_xticklabels([])  # clear out overlapping xlabels
    bpAx.set_yticks([])  # don't need that 1 tick mark
    plt.xlabel('Distance between particles (nm)')
    plt.ylabel('Number of observations')
    bpAx.set_title('Histogram and boxplot of distances between particles {} and {}'.format(part1, part2))
    plt.show()

