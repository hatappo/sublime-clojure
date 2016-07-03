#!/usr/bin/env inlein

'{:dependencies [[org.clojure/clojure "1.8.0"]
                 [enlive "1.1.6"]]}

(require '[net.cgrand.enlive-html :as html])
(require '[clojure.java.io :as io])
(require '[clojure.string :as s])

(def url "http://cljs.github.io/api/")

(def namespace-selector [:h4 :> :a html/text-node])

(def var-selector [:span :> :a])

(let [nodes (html/html-resource (io/reader url))]
  (->> (html/select nodes namespace-selector)
       (filter #(re-matches #"^(cljs\.|clojure\.).*" %))
       (s/join "\",\"")
       (printf "\"%s\","))
  (println "\n")
  (->> (html/select nodes var-selector)
       (map (fn [scraped] {:text (s/join "" (:content scraped))
                           :href (get-in scraped [:attrs :href])}))
       (filter #(and (< 1 (count (:text %)))
                     (re-matches #"^/api/(special|cljs\.|clojure\.).*" (:href %))))
       (map #(:text %))
       (s/join "\",\"")
       (printf "\"%s\","))
       ; prn)
  (println "\n"))
