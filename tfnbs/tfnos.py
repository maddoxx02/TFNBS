import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components


def get_tfce_score(t_stats, e, h, n, start_thres=1.65):
    """ Transform the connectivity matrix using Threshold-Free Network-Oriented Statistics.

    Parameters:
        statsmat (numpy.ndarray): The statistic matrix to be transformed.
        e (float ): Extent exponent (a scalar).
        h (float ): Height exponent (a scalar).
        n (int): Number of steps for cluster formation.

    Returns:
        numpy.ndarray: Transformed TFNOS scores.
    """
    # Input validation: Diagonal elements must be zero (no self-connections)

    try:
        import networkx as nx
    except ImportError:
        print(
            "Error: networkx is required to use this function.  It should have been installed with the package, "
            "but something went wrong.  Please try reinstalling the package or installing networkx manually.")

    if not np.all(np.diag(t_stats) == 0):
        raise ValueError("Diagonal elements of the connectivity matrix must be zero (no self-connections).")

        # Set cluster thresholds
        # Initialize output array
    # Convert e and h to lists if they are single float values
    scalar_mode = np.isscalar(e) and np.isscalar(h)
    if scalar_mode:
        e, h = [e], [h]  # Convert to lists for unified processing

    # Ensure e and h are arrays and have the same length
    e = np.array(e)
    h = np.array(h)
    if e.shape != h.shape:
        raise ValueError("e and h must have the same shape!")

    # Matrix size and output initialization
    nroi = t_stats.shape[0]
    num_params = len(e)
    tfnos_shape = (nroi, nroi) if scalar_mode else (nroi, nroi, num_params)
    tfnos = np.zeros(tfnos_shape)
    # Compute thresholds
    max_stat = np.max(t_stats)
    dh = (max_stat - start_thres) / n
    if dh == 0:
        return tfnos  # Return zero matrix if no variation
    # threshs = np.linspace(dh, max_stat, n)
    threshs = np.linspace(start_thres+dh, max_stat, n)

    # Reshape e and h for broadcasting (only if in multi-value mode)
    if not scalar_mode:
        e = e.reshape(1, 1, num_params)
        h = h.reshape(1, 1, num_params)

    for threshold in threshs:
        mask = t_stats >= threshold
        np.fill_diagonal(mask, False)
        G = nx.from_numpy_array(mask)
        components = list(nx.connected_components(G))
        clustsize = 1. * mask.copy()
        for component in components:
            if len(component) >= 2:
                sz_links = np.sum(mask[np.ix_(list(component), list(component))]) / 2
                clustsize[np.ix_(list(component), list(component))] *= sz_links
        np.fill_diagonal(clustsize, 0)

        # Compute TFCE scores
        if scalar_mode:
            tfnos += (clustsize ** e[0]) * (threshold ** h[0])
        else:
            tfnos += (clustsize[..., np.newaxis] ** e) * (threshold ** h)

    tfnos = tfnos * dh
    return tfnos


def get_tfce_score_scipy(t_stats, e, h, n, start_thres=1.65):
    """
    Transform the connectivity matrix using Threshold-Free Network-Oriented Statistics.

    Parameters:
        t_stats (np.ndarray): The statistic matrix (N x N).
        e (float or list of float): Extent exponent(s).
        h (float or list of float): Height exponent(s).
        n (int): Number of steps for cluster formation.
        start_thres (float) : Threshold value (a scalar) start for integration

    Returns:
        np.ndarray: Transformed TFNOS scores with shape (N, N, len(e_list)).

    """
    if not np.all(np.diag(t_stats) == 0):
        raise ValueError("Diagonal elements of the connectivity matrix must be zero (no self-connections).")

    # Convert e and h to lists if they are single float values
    scalar_mode = np.isscalar(e) and np.isscalar(h)
    if scalar_mode:
        e, h = [e], [h]  # Convert to lists for unified processing

    # Ensure e and h are arrays and have the same length
    e = np.array(e)
    h = np.array(h)
    if e.shape != h.shape:
        raise ValueError("e and h must have the same shape!")

    # Matrix size and output initialization
    nroi = t_stats.shape[0]
    num_params = len(e)
    tfnos_shape = (nroi, nroi) if scalar_mode else (nroi, nroi, num_params)
    tfnos = np.zeros(tfnos_shape)

    # Compute thresholds
    max_stat = np.max(t_stats)
    dh = (max_stat-start_thres) / n
    if dh == 0:
        return tfnos  # Return zero matrix if no variation
    #threshs = np.linspace(dh, max_stat, n)
    threshs = np.linspace(start_thres+dh, max_stat, n)

    # Reshape e and h for broadcasting (only if in multi-value mode)
    if not scalar_mode:
        e = e.reshape(1, 1, num_params)
        h = h.reshape(1, 1, num_params)


    # Use sparse matrix and connected components for efficiency
    for threshold in threshs:
        mask = t_stats >= threshold
        np.fill_diagonal(mask, False)
        n_components, labels = connected_components(mask.astype(int), directed=False)

        # Compute cluster sizes
        unique, counts = np.unique(labels, return_counts=True)
        clustsize = 1.*mask.copy()

        for lbl, size in zip(unique, counts):
            if size >= 2:  # Ignore single-node clusters
                sz_links = np.sum(mask[np.ix_(labels == lbl, labels == lbl)]) / 2
                clustsize[np.ix_(labels == lbl, labels == lbl)] *= sz_links
            # TFNOS accumulation
        np.fill_diagonal(clustsize, 0)

        # Compute TFCE scores
        if scalar_mode:
            tfnos += (clustsize ** e[0]) * (threshold ** h[0])
        else:
            tfnos += (clustsize[..., np.newaxis] ** e) * (threshold ** h)

    tfnos *= dh
    return tfnos

