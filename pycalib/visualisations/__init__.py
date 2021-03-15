import numpy as np
import itertools

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import label_binarize
from sklearn.calibration import calibration_curve

from sklearn.preprocessing import label_binarize
from sklearn.calibration import calibration_curve
from statsmodels.stats.proportion import proportion_confint

from matplotlib import gridspec


def plot_reliability_diagram(labels, scores_list, legend, show_histogram=True,
                             bins=10, class_names=None, fig=None,
                             show_counts=False, errorbar_interval=None,
                             interval_method='beta', fmt='s-',
                             show_correction=False,
                             show_samples=False,
                             sample_proportion=1.0,
                             hist_per_class=False):
    '''
    Parameters
    ==========
    labels : array (n_samples, )
        Labels indicating the ground class
    scores_list : list of matrices [(n_samples, n_classes)]
        Output probability scores for every method
    legend : list of strings
        Text to use for the legend
    n_bins : int
        Number of bins to create in the scores' space
    histogram : boolean
        If True, it generates an additional figure showing the number of
        samples in each bin.

    Regurns
    =======
    fig : matplotlib.pyplot.figure
        Figure with the reliability diagram
    '''
    classes = np.unique(labels)
    n_classes = len(classes)
    labels = label_binarize(labels, classes=classes)

    if class_names is None:
        if n_classes == 2:
            class_names = ['2']
        else:
            class_names = [str(i+1) for i in range(n_classes)]

    if n_classes == 2:
        scores_list = [score[:, 1].reshape(-1, 1) for score in scores_list]
        class_names = [class_names[1], ]

    n_columns = labels.shape[1]

    if fig is None:
        fig = plt.figure(figsize=(n_columns*4, 4))

    if show_histogram:
        spec = gridspec.GridSpec(ncols=n_columns, nrows=2,
                                 height_ratios=[5, 1],
                                 wspace=0.01, hspace=0.04)
    else:
        spec = gridspec.GridSpec(ncols=1, nrows=1)

    if isinstance(bins, int):
        n_bins = bins
        bins = np.linspace(0, 1 + 1e-8, n_bins)
    elif isinstance(bins, list) or isinstance(bins, np.ndarray):
        n_bins = len(bins) - 1

    for i in range(n_columns):
        ax1 = fig.add_subplot(spec[i])

        for score, name in zip(scores_list, legend):
            bin_idx = np.digitize(score[:, i], bins) - 1

            bin_true = np.bincount(bin_idx, weights=labels[:, i], minlength=n_bins)
            bin_pred = np.bincount(bin_idx, weights=score[:, i], minlength=n_bins)
            bin_total = np.bincount(bin_idx, minlength=n_bins)

            avg_true = np.divide(bin_true, bin_total)
            avg_pred = np.divide(bin_pred, bin_total)

            if errorbar_interval is None:
                p = ax1.plot(avg_pred, avg_true, fmt, label=name)
                color = p[0].get_color()
            else:
                intervals = proportion_confint(count=bin_true, nobs=bin_total,
                                               alpha=1-errorbar_interval,
                                               method=interval_method)
                intervals = np.array(intervals)
                yerr = intervals - avg_true
                yerr = np.abs(yerr)
                ebar  = ax1.errorbar(avg_pred, avg_true, yerr=yerr,
                                    label=name, fmt=fmt, markersize=5)
                color = ebar[0].get_color()

            if show_counts:
                for ap, at, count in zip(avg_pred, avg_true, bin_total):
                    if np.isfinite(ap) and np.isfinite(at):
                        ax1.text(ap, at, str(count), fontsize=8, ha='center', va='center',
                                bbox=dict(boxstyle='square,pad=0.15', fc='white',
                                          ec=color))

            if show_correction:
                for ap, at in zip(avg_pred, avg_true):
                    ax1.arrow(ap, at, at - ap, 0, color='red', head_width=0.02,
                             length_includes_head=True)

            if show_samples:
                idx = np.random.choice(labels.shape[0], int(sample_proportion*labels.shape[0]))
                ax1.scatter(score[idx, i], labels[idx, i], marker='d', s=100,
                           alpha=0.1)

        ax1.plot([0, 1], [0, 1], "r--")
        ax1.set_xlim([0, 1])
        ax1.set_ylim([0, 1])
        #ax1.set_title('Class {}'.format(class_names[i]))
        ax1.set_xlabel('Mean predicted value (Class {})'.format(
            class_names[i]))
        if i == 0:
            ax1.set_ylabel('Fraction of positives')
        ax1.grid(True)

        if show_histogram:
            ax1.get_xaxis().set_visible(False)
            lines = ax1.get_lines()
            #ax2.set_xticklabels([])
            ax2 = fig.add_subplot(spec[n_columns + i])
            for j, (score, name) in enumerate(zip(scores_list, legend)):
                color = lines[j].get_color()
                if hist_per_class:
                    for c in [0, 1]:
                        linestyle = ('solid','dashed')[c]
                        ax2.hist(score[labels[:, i]==c, i], range=(0, 1), bins=bins, label=name,
                                 histtype="step", lw=2, linestyle=linestyle, color=color)
                else:
                    ax2.hist(score[:, i], range=(0, 1), bins=bins, label=name,
                             histtype="step", lw=2)
                ax2.set_xlim([0, 1])
                ax2.set_xlabel('Mean predicted value (Class {})'.format(
                    class_names[i]))
                if i == 0:
                    ax2.set_ylabel('#count')
                ax2.grid(True)

    lines, labels = fig.axes[0].get_legend_handles_labels()
    fig.legend(lines, labels, loc='upper center', bbox_to_anchor=(0, 0, 1, 1),
               bbox_transform=fig.transFigure, ncol=6)

    return fig


def plot_binary_reliability_diagram_gaps(y_true, p_pred, n_bins=15, title=None,
                                         fig=None, ax=None, legend=True):
    '''Plot binary reliability diagram gaps

    Parameters
    ==========
    y_true : np.array shape (n_samples, 2) or (n_samples, )
        Labels corresponding to the scores as a binary indicator matrix or as a
        vector of integers indicating the class.
    p_pred : binary matrix shape (n_samples, 2) or (n_samples, )
        Output probability scores for each class as a matrix, or for the
        positive class
    n_bins : integer
        Number of bins to divide the scores
    title : string
        Title for the plot
    fig : matplotlib.pyplot.figure
        Plots the axis in the given figure
    ax : matplotlib.pyplot.Axis
        Axis where to draw the plot
    legend : boolean
        If True the function will draw a legend

    Regurns
    =======
    fig : matplotlib.pyplot.figure
        Figure with the reliability diagram
    '''
    if fig is None and ax is None:
        fig = plt.figure()
    if ax is None:
        ax = fig.add_subplot(111)

    if title is not None:
        ax.set_title(title)

    if (len(y_true.shape) == 2) and (y_true.shape[1] == 2):
        y_true = y_true[:, 1]
    if (len(y_true.shape) == 2) and (y_true.shape[1] > 2):
        raise ValueError('y_true wrong dimensions {}'.format(y_true.shape))

    if (len(p_pred.shape) == 2) and (p_pred.shape[1] == 2):
        p_pred = p_pred[:, 1]
    if (len(p_pred.shape) == 2) and (p_pred.shape[1] > 2):
        raise ValueError('p_pred wrong dimensions {}'.format(p_pred.shape))

    bin_size = 1.0/n_bins
    centers = np.linspace(bin_size/2.0, 1.0 - bin_size/2.0, n_bins)
    true_proportion = np.zeros(n_bins)
    pred_mean = np.zeros(n_bins)
    for i, center in enumerate(centers):
        if i == 0:
            # First bin includes lower bound
            bin_indices = np.where(np.logical_and(p_pred >= center - bin_size/2,
                                                  p_pred <= center +
                                                  bin_size/2))
        else:
            bin_indices = np.where(np.logical_and(p_pred > center - bin_size/2,
                                                  p_pred <= center +
                                                  bin_size/2))
        if len(bin_indices[0]) == 0:
            true_proportion[i] = np.nan
            pred_mean[i] = np.nan
        else:
            true_proportion[i] = np.mean(y_true[bin_indices])
            pred_mean[i] = np.nanmean(p_pred[bin_indices])

    not_nan = np.isfinite(true_proportion - centers)
    ax.bar(centers, true_proportion, width=bin_size, edgecolor="black",
           color="blue", label='True class prop.')
    ax.bar(pred_mean[not_nan], (true_proportion - pred_mean)[not_nan],
           bottom=pred_mean[not_nan], width=bin_size/4.0, edgecolor="red",
           color="#ffc8c6",
           label='Gap pred. mean')
    ax.scatter(pred_mean[not_nan], true_proportion[not_nan], color='red',
               marker="+", zorder=10)

    if legend:
        ax.legend()

    ax.plot([0, 1], [0, 1], linestyle="--")
    ax.set_xlim([0, 1])
    ax.set_xlabel('Predicted probability')
    ax.set_ylim([0, 1])
    ax.set_ylabel('Proportion of positives')
    ax.grid(True)
    ax.set_axisbelow(True)

    return fig, ax


def plot_multiclass_reliability_diagram_gaps(y_true, p_pred, fig=None, ax=None,
                                             per_class=True, **kwargs):

    if len(y_true.shape) < 2 or y_true.shape[1] == 1:
        ohe = OneHotEncoder(categories='auto')
        ohe.fit(y_true.reshape(-1, 1))
        y_true = ohe.transform(y_true.reshape(-1,1))

    if per_class:
        n_classes = y_true.shape[1]
        if fig is None and ax is None:
            fig = plt.figure(figsize=((n_classes-1)*4, 4))
        if ax is None:
            ax = [fig.add_subplot(1, n_classes, i+1) for i in range(n_classes)]
        for i in range(n_classes):
            if i == 0:
                legend=True
            else:
                legend=False
            plot_binary_reliability_diagram_gaps(y_true[:,i], p_pred[:,i],
                                                 title='$C_{}$'.format(i+1),
                                                 fig=fig, ax=ax[i],
                                                 legend=legend,
                                                 **kwargs)
            if i > 0:
                ax[i].set_ylabel('')
            ax[i].set_xlabel('Predicted probability')
    else:
        if fig is None and ax is None:
            fig = plt.figure()
        mask = p_pred.argmax(axis=1)
        indices = np.arange(p_pred.shape[0])
        y_true = y_true[indices, mask].T
        p_pred = p_pred[indices, mask].T
        ax = fig.add_subplot(1, 1, 1)
        plot_binary_reliability_diagram_gaps(y_true, p_pred,
                                             title=r'$C_1$',
                                             fig=fig, ax=ax, **kwargs)
        ax.set_title('')

    return fig

def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues,
                          fig=None, ax=None):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if fig is None:
        fig = plt.figure()

    if ax is None:
        ax = fig.add_subplot(111)

    if title is not None:
        ax.set_title(title)

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    im = ax.imshow(cm, interpolation='nearest', cmap=cmap)

    # create an axes on the right side of ax. The width of cax will be 5%
    # of ax and the padding between cax and ax will be fixed at 0.05 inch.
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)

    fig.colorbar(im, cax=cax)

    tick_marks = np.arange(len(classes))
    ax.set_xticks(tick_marks)
    ax.set_xticklabels(classes, rotation=45)
    ax.set_yticks(tick_marks)
    ax.set_yticklabels(classes)

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        ax.text(j, i, format(cm[i, j], fmt),
                horizontalalignment="center",
                color="white" if cm[i, j] > thresh else "black")

    ax.set_ylabel('True label')
    ax.set_xlabel('Predicted label')
    return fig

def plot_weight_matrix(weights, bias, classes, title='Weight matrix',
                       cmap=plt.cm.Greens, fig=None, ax=None, **kwargs):
    """
    This function prints and plots the weight matrix.
    """
    if fig is None:
        fig = plt.figure()

    if ax is None:
        ax = fig.add_subplot(111)

    if title is not None:
        ax.set_title(title)

    matrix = np.hstack((weights, bias.reshape(-1, 1)))

    im = ax.imshow(matrix, interpolation='nearest', cmap=cmap, **kwargs)

    # create an axes on the right side of ax. The width of cax will be 5%
    # of ax and the padding between cax and ax will be fixed at 0.05 inch.
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)

    fig.colorbar(im, cax=cax)

    tick_marks = np.arange(len(classes))
    ax.set_yticks(tick_marks)
    ax.set_yticklabels(classes)
    ax.set_xticks(np.append(tick_marks, len(classes)))
    ax.set_xticklabels(np.append(classes, 'c'))

    fmt = '.2f'
    thresh = matrix.max() / 2.
    for i, j in itertools.product(range(matrix.shape[0]), range(matrix.shape[1])):
        ax.text(j, i, format(matrix[i, j], fmt),
                 horizontalalignment="center",
                 verticalalignment="center",
                 color="white" if matrix[i, j] > thresh else "black")

    ax.set_ylabel('Class')
    return fig


def plot_individual_pdfs(class_dist, x_grid=None, y_grid=None,
                         grid_levels = 200, fig=None, title=None,
                         cmaps=None, grid=True):
    if fig is None:
        fig = plt.figure()

    if x_grid is None:
        x_grid = np.linspace(-8, 8, grid_levels)
    else:
        grid_levels = len(x_grid)

    if y_grid is None:
        y_grid = np.linspace(-8, 8, grid_levels)

    xx, yy = np.meshgrid(x_grid, y_grid)

    if cmaps is None:
        cmaps = [None]*len(class_dist.priors)

    for i, (p, d) in enumerate(zip(class_dist.priors, class_dist.distributions)):
        z = d.pdf(np.vstack([xx.flatten(), yy.flatten()]).T)

        ax = fig.add_subplot(1, len(class_dist.distributions), i+1)
        if title is None:
            ax.set_title('$P(Y={})={:.2f}$\n{}'.format(i+1, p, str(d)), loc='left')
        else:
            ax.set_title(title[i])
        contour = ax.contourf(xx, yy, z.reshape(grid_levels,grid_levels),
                              cmap=cmaps[i])
        if grid:
            ax.grid()
        fig.colorbar(contour)

    return fig


def plot_critical_difference(avranks, num_datasets, names,
                               title=None, test='bonferroni-dunn'):
    '''
        test: string in ['nemenyi', 'bonferroni-dunn']
         - nemenyi two-tailed test (up to 20 methods)
         - bonferroni-dunn one-tailed test (only up to 10 methods)

    '''
    # Critical difference plot
    import Orange

    if len(avranks) > 10:
        print('Forcing Nemenyi Critical difference')
        test = 'nemenyi'
    cd = Orange.evaluation.compute_CD(avranks, num_datasets, alpha='0.05',
                                      test=test)
    Orange.evaluation.graph_ranks(avranks, names, cd=cd, width=6,
                                  textspace=1.5)
    fig = plt.gcf()
    fig.suptitle(title, horizontalalignment='left')
    return fig


def plot_df_to_heatmap(df, title=None, figsize=None, annotate=True,
                 normalise_columns=False, normalise_rows=False, cmap=None):
    ''' Exports a heatmap of the given pandas DataFrame

    Parameters
    ----------
    df:     pandas.DataFrame
        It should be a matrix, it can have multiple index and these will be
        flattened.

    title: string
        Title of the figure

    figsize:    tuple of ints (x, y)
        Figure size in inches

    annotate:   bool
        If true, adds numbers inside each box
    '''
    if normalise_columns:
        df = df_normalise(df, columns=True)
    if normalise_rows:
        df = df_normalise(df, columns=False)

    yticklabels = multiindex_to_strings(df.index)
    xticklabels = multiindex_to_strings(df.columns)
    if figsize is not None:
        fig = plt.figure(figsize=figsize)
    else:
        point_inch_ratio = 72.
        n_rows = df.shape[0]
        font_size_pt = plt.rcParams['font.size']
        xlabel_space_pt = max([len(xlabel) for xlabel in xticklabels])
        fig_height_in = ((xlabel_space_pt + n_rows) * (font_size_pt + 3)) / point_inch_ratio

        n_cols = df.shape[1]
        fig_width_in = df.shape[1]+4
        ylabel_space_pt = max([len(ylabel) for ylabel in yticklabels])
        fig_width_in = ((ylabel_space_pt + (n_cols * 3) + 5)
                        * (font_size_pt + 3)) / point_inch_ratio
        fig = plt.figure(figsize=(fig_width_in, fig_height_in))

    ax = fig.add_subplot(111)
    if title is not None:
        ax.set_title(title)
    cax = ax.pcolor(df, cmap=cmap)
    fig.colorbar(cax)
    ax.set_yticks(np.arange(0.5, len(df.index), 1))
    ax.set_yticklabels(yticklabels)
    ax.set_xticks(np.arange(0.5, len(df.columns), 1))
    ax.set_xticklabels(xticklabels, rotation=45, ha="right")

    middle_value = (df.max().max() + df.min().min())/2.0
    if annotate:
        for y in range(df.shape[0]):
            for x in range(df.shape[1]):
                color = 'white' if middle_value > df.values[y, x] else 'black'
                plt.text(x + 0.5, y + 0.5, '%.2f' % df.values[y, x],
                         horizontalalignment='center',
                         verticalalignment='center',
                         color=color
                         )
    return fig