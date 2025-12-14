#
# Copyright (c) 2020 Pangeanic SL.
#
# This file is part of NEC TM
# (see https://github.com/shasha79/nectm).
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
import pytensor
import numpy
import os

from pytensor import tensor as pt
from collections import OrderedDict

'''
modified by Liangyou Li @ 25 July 2016
'''


class LSTM(object):
    
    '''
    nh :: dimension of the hidden layer
    de :: dimension of the word embeddings
    x  :: input sentence in two-dimension: sent_len * de
    '''
    
    def __init__(self, nh, de, x, suffix):
        
        # parameters
        self.wifoc = pytensor.shared(0.2*numpy.random.uniform(-1.0, 1.0,\
                    (de, 4*nh)).astype(pytensor.config.floatX))
        self.uifoc = pytensor.shared(0.2*numpy.random.uniform(-1.0, 1.0,\
                    (nh, 4*nh)).astype(pytensor.config.floatX))
        self.bifoc = pytensor.shared(numpy.zeros(4*nh).astype(pytensor.config.floatX))
        self.h0 = pytensor.shared(numpy.zeros(nh,).astype(pytensor.config.floatX))
        self.c0 = pytensor.shared(numpy.zeros(nh,).astype(pytensor.config.floatX))
         
        # bundle
        self.params = [ self.wifoc, self.uifoc, self.bifoc, self.h0, self.c0 ]
        self.names = ['wifoc_'+suffix, 'uifoc_'+suffix, 'bifoc_'+suffix, 'h0_'+suffix, 'c0_'+suffix]
        

        def _slice(data, index, size):
            return data[index*size:(index+1)*size]
    
        # rnn step   
        def recurrence(precomp_x_t, h_tm1, c_tm1):
            # i f o c
            precomp = precomp_x_t + pt.dot(h_tm1, self.uifoc)
            
            # input gate
            it = pt.sigmoid(_slice(precomp, 0, nh))
            ctt = pt.tanh(_slice(precomp, 3, nh))
            # forget gate
            ft = pt.sigmoid(_slice(precomp, 1, nh))
            
            # new memory cell
            ct = it*ctt + ft*c_tm1
            
            #output gate
            ot = pt.sigmoid(_slice(precomp, 2, nh))
            
            # new hidden state, a vector
            ht = ot * pt.tanh(ct)
            
            return [ht, ct]
        
        # precomputation for speed-up
        precomp_x = pt.dot(x, self.wifoc) + self.bifoc
        
        '''
        pytensor.scan read a sentence word by word
        call the function recurrence to:
            process each word
            return values
        '''
        [h_sent, c_sent] , _ = pytensor.scan(fn=recurrence,\
                sequences=[precomp_x], outputs_info=[self.h0, self.c0])
        
        # new sentence representation in two dimension: sent_len * nh
        self.hidden = h_sent.reshape((x.shape[0], nh))



class model(object):
    
    def __init__(self, nh, nc, ne, de, cs):
        '''
        nh :: dimension of the hidden layer
        nc :: number of classes
        ne :: number of word embeddings in the vocabulary
        de :: dimension of the word embeddings
        cs :: word window context size 
        '''
        
        nctxt = 2*nh
        
        # parameters of the model
        self.emb = pytensor.shared(0.2 * numpy.random.uniform(-1.0, 1.0,\
                   (ne+1, de)).astype(pytensor.config.floatX)) # add one for PADDING at the end
        self.W   = pytensor.shared(0.2 * numpy.random.uniform(-1.0, 1.0,\
                   (nh, nc)).astype(pytensor.config.floatX))
        self.b   = pytensor.shared(numpy.zeros(nc, dtype=pytensor.config.floatX))
        
        self.wifoc = pytensor.shared(0.2*numpy.random.uniform(-1.0, 1.0,\
                    (de*cs, 4*nh)).astype(pytensor.config.floatX))
        self.uifoc = pytensor.shared(0.2*numpy.random.uniform(-1.0, 1.0,\
                    (nh, 4*nh)).astype(pytensor.config.floatX))
        self.bifoc = pytensor.shared(numpy.zeros(4*nh).astype(pytensor.config.floatX))
        self.h0 = pytensor.shared(numpy.zeros(nh,).astype(pytensor.config.floatX))
        self.c0 = pytensor.shared(numpy.zeros(nh,).astype(pytensor.config.floatX))
        self.Watt  = pytensor.shared(0.2*numpy.random.uniform(-1.0, 1.0,\
                    (de*cs, nctxt)).astype(pytensor.config.floatX))
        self.batt = pytensor.shared(numpy.zeros(nctxt).astype(pytensor.config.floatX))
        
        # parameters of source context
        self.emb_ctxt = pytensor.shared(0.2 * numpy.random.uniform(-1.0, 1.0,\
                        (ne, de)).astype(pytensor.config.floatX)) # add one for PADDING at the end
        self.h2c = pytensor.shared(0.2 * numpy.random.uniform(-0.1, 0.1,\
                    (nh,nctxt)).astype(pytensor.config.floatX))
        self.Wctxt = pytensor.shared(0.2 * numpy.random.uniform(-0.1, 0.1,\
                    (nctxt,1)).astype(pytensor.config.floatX))
        self.bctxt   = pytensor.shared(numpy.zeros((1,), dtype=pytensor.config.floatX))
        self.Wcv = pytensor.shared(0.2 * numpy.random.uniform(-0.1, 0.1,\
                    (nctxt,4*nh)).astype(pytensor.config.floatX))
        self.c2c = pytensor.shared(0.2 * numpy.random.uniform(-0.1, 0.1,\
                    (nctxt,nctxt)).astype(pytensor.config.floatX))
        
        # vector representation of labels
        s = [ [1,0,0],
              [0,1,0],
              [0,0,1]
            ]
        self.emb_label = pytensor.shared(numpy.array(s, dtype=pytensor.config.floatX))
        
        '''
        z: source sentence, a vector
        zy: source sentence label, a vector
        '''
        z = pt.ivector()
        zy = pt.ivector()
        
        '''
        ctxt: source, a matrix: sent_len * (de + nc)
        ctxt_rev: reversed source, a matrix: sent_len * (de + nc)
        
        word representation and label representation are concatenated
        '''
        
        ctxt = pt.concatenate([self.emb_ctxt[z], self.emb_label[zy]], axis=1)
        ctxt_rev = pt.concatenate([self.emb_ctxt[z[::-1]], self.emb_label[zy[::-1]]], axis=1)
        
        '''
        forward and backward LSTM to compute representation of each source word
        '''
        self.lstmfwd = LSTM(nh, de+nc, ctxt, "fwd")
        self.lstmbwd = LSTM(nh, de+nc, ctxt_rev, "bwd")
        
        '''
        concatenate the two LSTM to get a full representation of each source word
        '''
        self.context = pt.concatenate([self.lstmfwd.hidden, self.lstmbwd.hidden[::-1]], axis=1)

        # bundle parameters which will be tuned
        self.params = [ self.emb, self.W, self.b, self.wifoc, self.uifoc, self.bifoc, self.h0, self.c0, self.Watt, self.batt ]\
                        + [self.emb_ctxt, self.h2c, self.Wctxt, self.bctxt, self.Wcv, self.c2c] \
                        + self.lstmfwd.params + self.lstmbwd.params
        self.names  = ['embeddings', 'W', 'b', 'Wifoc', 'Uifoc', 'bifoc', 'h0', 'c0', 'Watt', 'batt']\
                        + ['embeddings_src', 'h2c', 'Wctxt', 'bctxt', 'Wcv', 'Wc2c'] \
                        + self.lstmfwd.names + self.lstmbwd.names
        '''
        target sentence
        each target word is accompanied with context words, see the finction contextwin in tools.py
        '''
        idxs = pt.imatrix() 
        x = self.emb[idxs].reshape((idxs.shape[0], de*cs))
        # target labels
        y    = pt.ivector('y') # label
        
        def _slice(data, index, size):
            return data[index*size:(index+1)*size]
        
        '''
        target recurrent neural network, LSTM
        use attention to source sentence
        '''
        def recurrence(attx_t, precomp_x_t, h_tm1, c_tm1, ctxt_tm1):
            
            '''
            attention model
            a distribution over source words
            '''
            pre_ctxt = pt.dot(h_tm1, self.h2c) + attx_t + pt.dot(ctxt_tm1, self.c2c)
            ctxt = self.context + pre_ctxt[None,:] 
            ctxt = pt.tanh(ctxt)
            alpha = pt.dot(ctxt, self.Wctxt) + self.bctxt#.repeat(ctxt.shape[0],axis=0)
            alpha = pt.exp(alpha.reshape((alpha.shape[0],)))
            alpha = alpha / pt.sum(alpha)
            
            '''
            weighted sum of source words
            '''
            cv = (self.context * alpha[:,None]).sum(axis=0) # 2h
            
            
            precomp = precomp_x_t + pt.dot(h_tm1, self.uifoc) + pt.dot(cv, self.Wcv)
            
            # LSTM gates
            it = pt.sigmoid(_slice(precomp, 0, nh))
            ctt = pt.tanh(_slice(precomp, 3, nh))
            ft = pt.sigmoid(_slice(precomp, 1, nh))
            
            c_t = it*ctt + ft*c_tm1
            
            ot = pt.sigmoid(_slice(precomp, 2, nh))
            
            # new hidden
            h_t = ot * pt.tanh(c_t)
            
            # softmax to calculate a distribution over labels
            s_t = pt.special.softmax(pt.dot(h_t, self.W) + self.b)
            return [h_t, c_t, cv, s_t]
        
        # precomputation to speed-up
        precomp_x = pt.dot(x, self.wifoc) + self.bifoc
        att_x = pt.dot(x, self.Watt) + self.batt
        ctxt_init = pt.mean(self.context, axis=0)
        
        # pytensor.scan over target sentence word by word
        [h, _, _, s], _ = pytensor.scan(fn=recurrence, \
            sequences=[att_x, precomp_x], outputs_info=[self.h0, self.c0, ctxt_init, None], \
            n_steps=x.shape[0])
        
        '''
        label probabilities of each target word
        '''
        # s is already shape (n_steps, nc) from scan, no need for s[:,0,:]
        p_y_given_x_sentence = s
        # take the one with the largest probability
        y_pred = pt.argmax(p_y_given_x_sentence, axis=1)

        # cost and gradients
        lr = pt.scalar('lr')
        nll = pt.mean(-pt.log(p_y_given_x_sentence[pt.arange(y.shape[0]), y]))
        gradients = pt.grad( nll, self.params )
        
        '''
        gradient clipping to prevent huge updates
        '''
        max_dw = 5.
        new_dw = pt.sum([(gparam**2).sum() for gparam in gradients])
        new_dw = pt.sqrt(new_dw)
        gradients = [gparam*pt.min([max_dw, new_dw])/new_dw for gparam in gradients]
        
        
        ####### adadelta, adaptive updates of parameters
        # create variables to store intermediate updates
        parameters = self.params
        rho = 0.95
        eps = 1e-6
        gradients_sq = [ pytensor.shared(numpy.zeros(p.get_value().shape).astype(pytensor.config.floatX)) for p in parameters ]
        deltas_sq = [ pytensor.shared(numpy.zeros(p.get_value().shape).astype(pytensor.config.floatX)) for p in parameters ]
     
        # calculates the new "average" delta for the next iteration
        gradients_sq_new = [ rho*g_sq + (1-rho)*(g**2) for g_sq,g in zip(gradients_sq,gradients) ]
     
        # calculates the step in direction. The square root is an approximation to getting the RMS for the average value
        deltas = [ (pt.sqrt(d_sq+eps)/pt.sqrt(g_sq+eps))*grad for d_sq,g_sq,grad in zip(deltas_sq,gradients_sq_new,gradients) ]
     
        # calculates the new "average" deltas for the next step.
        deltas_sq_new = [ rho*d_sq + (1-rho)*(d**2) for d_sq,d in zip(deltas_sq,deltas) ]
     
        # Prepare it as a list f
        gradient_sq_updates = list(zip(gradients_sq,gradients_sq_new))
        deltas_sq_updates = list(zip(deltas_sq,deltas_sq_new))
        parameters_updates = [ (p,p - d) for p,d in zip(parameters,deltas) ]
        updates = gradient_sq_updates + deltas_sq_updates + parameters_updates
        ##### end adadelta
        
        # pytensor functions
        self.classify = pytensor.function(inputs=[idxs, z, zy], outputs=y_pred)

        self.train = pytensor.function( inputs  = [idxs, y, z, zy],
                                      outputs = nll,
                                      updates = updates )
        
        # not used
        self.normalize = pytensor.function( inputs = [],
                         updates = [(self.emb,
                         self.emb/pt.sqrt((self.emb**2).sum(axis=1)).dimshuffle(0,'x')),\
                         (self.emb_ctxt,
                         self.emb_ctxt/pt.sqrt((self.emb_ctxt**2).sum(axis=1)).dimshuffle(0,'x'))])
    
    '''
    save model to a given folder
    '''
    def save(self, folder):   
        for param, name in zip(self.params, self.names):
            numpy.save(os.path.join(folder, name + '.npy'), param.get_value())
    '''
    load model from a given folder
    '''
    def load(self, folder):   
        for param, name in zip(self.params, self.names):
            param.set_value(numpy.load(os.path.join(folder, name + '.npy')))
