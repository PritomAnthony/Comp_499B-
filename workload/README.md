 The structure of the workload input adheres to the following format. Please note that all communication sizes are measured in bytes and compute times are denoted in cycles:

* **First Line**: (DATA/HYBRID_TRANSFORMER/HYBRID_DLRM)
  * This line specifies the type of training loop parallelization. DATA refers to a purely data-parallel approach, HYBRID_TRANSFORMER denotes a hybrid-parallel approach tailored for Transformer DNN networks, while HYBRID_DLRM implies a hybrid-parallel approach fine-tuned for DLRM DNN networks.

* **Second Line**: (int)
  * This line indicates the number of layers in the DNN.

* **Subsequent Lines**: Each subsequent line describes a layer. The format of layer description  is as follows:
  * {(string: **layer name**) (int: **reserved variable**) (int: **forward pass compute time**) (ALLREDUCE/ALLGATHER/ALLTOALL: **forward pass communication type**) (int: **forward pass communication size**) (int: **input grad compute time**) (ALLREDUCE/ALLGATHER/ALLTOALL: **input grad communication type**) (int: **input grad communication size**) (int: **weight grad compute time**) (ALLREDUCE/ALLGATHER/ALLTOALL: **weight grad communication type**) (int: **weight grad communication size**) (**delay per entire weight/input/output update after the collective is finished**)}



*NOTE: All parameters within the brackets are defined on a single line for each layer of the DNN network.* 
    * **layer name**: A string representing the name of the layer.
    * **reserved variable**: An integer reserved for future use or specific configurations.
    * **forward pass compute time**: An integer denoting the compute time for the forward pass in cycles.
    * **forward pass communication type**: The type of communication used during the forward pass, which can be ALLREDUCE, ALLGATHER, or ALLTOALL.
    * **forward pass communication size**: An integer indicating the size of communication during the forward pass in bytes.
    * **input grad compute time**: An integer representing the compute time for input gradients in cycles.
    * **input grad communication type**: The type of communication used for input gradients, which can be ALLREDUCE, ALLGATHER, or ALLTOALL.
    * **input grad communication size**: An integer specifying the size of communication for input gradients in bytes.
    * **weight grad compute time**: An integer indicating the compute time for weight gradients in cycles.
    * **weight grad communication type**: The type of communication used for weight gradients, which can be ALLREDUCE, ALLGATHER, or ALLTOALL.
    * **weight grad communication size**: An integer denoting the size of communication for weight gradients in bytes.
    * **delay per entire weight/input/output update after the collective is finished**: An integer representing any additional delay after the completion of collective operations.