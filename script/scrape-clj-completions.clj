#!/usr/bin/env inlein

'{:dependencies [[org.clojure/clojure "1.8.0"]
                 [enlive "1.1.6"]]}

(require '[net.cgrand.enlive-html :as html])
(require '[clojure.java.io :as io])
(require '[clojure.string :as s])

(def url "https://clojuredocs.org/core-library/vars")

(def namespace-selector [:ul.nav :> :li :> :a html/text-node])

(def var-selector [:ul.var-list :> :li :> :a html/text-node])

(let [nodes (html/html-resource (io/reader url))]
  (->> (html/select nodes namespace-selector)
       (filter #(s/starts-with? % "clojure."))
       (s/join "\",\"")
       (printf "\"%s\","))
  (println "\n")
  (->> (html/select nodes var-selector)
       (filter #(< 1 (count %)))
       (s/join "\",\"")
       (printf "\"%s\","))
  (println "\n"))
